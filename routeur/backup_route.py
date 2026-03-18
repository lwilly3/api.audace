"""
Routes API pour la gestion des sauvegardes (Backup Management).

Prefix : /backup
Permission requise : can_manage_backups

Endpoints :
- GET  /backup/config              — Configuration actuelle
- PUT  /backup/config              — Modifier la configuration
- POST /backup/config/oauth/url    — Generer l'URL OAuth Google
- GET  /backup/config/oauth/callback — Callback OAuth (redirect navigateur)
- POST /backup/config/disconnect   — Deconnecter Google Drive
- POST /backup/trigger             — Declencher un backup manuel
- GET  /backup/status/{task_id}    — Statut d'une tache en cours
- GET  /backup/history             — Historique pagine
- GET  /backup/files               — Liste des fichiers de backup
- POST /backup/restore/{backup_id} — Declencher une restauration
"""

import glob
import logging
import os
import subprocess
import threading
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config.config import settings
from app.db.database import SessionLocal, get_db
from app.db.crud.crud_audit_logs import log_action
from app.db.crud.crud_backup import (
    create_backup_history,
    get_backup_by_id,
    get_backup_config,
    get_backup_history,
    update_backup_history,
    upsert_backup_config,
)
from app.models.model_user import User
from app.models.model_user_permissions import UserPermissions
from app.models.model_backup import BackupHistory
from app.schemas.schema_backup import (
    BackupConfigResponse,
    BackupConfigUpdate,
    BackupFileInfo,
    BackupHistoryPaginated,
    BackupHistoryResponse,
    BackupRestoreRequest,
    BackupRestoreResponse,
    BackupTriggerResponse,
    CreateFolderRequest,
    DriveFolderInfo,
    OAuthUrlResponse,
)
from app.services import sync_tasks
from app.services.google_drive_client import (
    build_google_auth_url,
    create_drive_folder,
    download_from_drive,
    ensure_valid_token,
    exchange_google_code,
    list_drive_files,
    list_drive_folders,
    upload_to_drive,
    verify_google_state,
)
from app.utils.crypto import encrypt_totp_secret
from core.auth.oauth2 import get_current_user

logger = logging.getLogger("hapson-api")

router = APIRouter(prefix="/backup", tags=["backup"])

# Dossier des backups locaux (monte via docker volume)
BACKUP_DIR = "/backups"


# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def _check_backup_permission(db: Session, user: User):
    """Verifie que l'utilisateur a la permission can_manage_backups.
    Les super_admin ont un acces automatique (bypass)."""
    # Bypass pour les super_admin (hierarchy_level 100)
    if hasattr(user, 'roles') and user.roles:
        for role in user.roles:
            if role.name == 'super_admin':
                return
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == user.id).first()
    if not perms or not perms.can_manage_backups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission 'can_manage_backups' requise"
        )


def _sync_drive_to_history(db: Session):
    """Synchronise les fichiers Google Drive vers backup_history.

    Apres une reinstallation du VPS, la table backup_history est vide
    mais les fichiers existent toujours sur Google Drive. Cette fonction
    cree des entrees 'completed' pour chaque fichier Drive absent de l'historique,
    permettant ainsi la restauration directe depuis l'UI.
    """
    try:
        config = get_backup_config(db)
        if not config or not config.is_connected or not config.google_drive_folder_id:
            return

        access_token = ensure_valid_token(db)
        if not access_token:
            return

        drive_files = list_drive_files(access_token, config.google_drive_folder_id)
        if not drive_files:
            return

        # Recuperer les google_drive_file_id deja connus en DB
        existing_ids = set()
        existing_records = db.query(BackupHistory.google_drive_file_id).filter(
            BackupHistory.google_drive_file_id.isnot(None)
        ).all()
        for record in existing_records:
            existing_ids.add(record[0])

        # Creer des entrees pour les fichiers Drive non connus
        new_count = 0
        for df in drive_files:
            file_id = df.get("id")
            if not file_id or file_id in existing_ids:
                continue

            filename = df.get("name", "unknown")
            file_size = int(df["size"]) if df.get("size") else None

            # Parser la date de modification du fichier Drive
            completed_at = None
            if df.get("modifiedTime"):
                try:
                    completed_at = datetime.fromisoformat(df["modifiedTime"].replace("Z", "+00:00"))
                except Exception:
                    completed_at = datetime.now(timezone.utc)

            entry = BackupHistory(
                filename=filename,
                file_size_bytes=file_size,
                backup_type="manual",
                status="completed",
                google_drive_file_id=file_id,
                uploaded_to_drive=True,
                started_at=completed_at or datetime.now(timezone.utc),
                completed_at=completed_at,
                duration_seconds=0,
                triggered_by=None,
            )
            db.add(entry)
            new_count += 1

        if new_count > 0:
            db.commit()
            logger.info(f"Sync Drive → DB : {new_count} fichier(s) importe(s) dans l'historique")

    except Exception as e:
        db.rollback()
        logger.warning(f"Erreur sync Drive → historique : {e}")


def _config_to_response(config, db: Session) -> BackupConfigResponse:
    """Convertit un BackupConfig en BackupConfigResponse."""
    if not config:
        return BackupConfigResponse()

    # Verifier si le token est valide
    token_valid = False
    if config.is_connected and config.google_token_expires_at:
        now = datetime.now(timezone.utc)
        token_valid = config.google_token_expires_at > now

    return BackupConfigResponse(
        is_connected=config.is_connected,
        google_email=config.google_email,
        google_drive_folder_id=config.google_drive_folder_id,
        google_drive_folder_name=config.google_drive_folder_name,
        auto_backup_enabled=config.auto_backup_enabled,
        auto_backup_hour=config.auto_backup_hour or 3,
        retention_days=config.retention_days or 30,
        connected_at=config.connected_at,
        token_valid=token_valid,
    )


# ════════════════════════════════════════════════════════════════
# CONFIG ENDPOINTS
# ════════════════════════════════════════════════════════════════

@router.get("/config", response_model=BackupConfigResponse)
def get_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne la configuration actuelle du backup."""
    _check_backup_permission(db, current_user)
    config = get_backup_config(db)
    return _config_to_response(config, db)


@router.put("/config", response_model=BackupConfigResponse)
def update_config(
    data: BackupConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Met a jour la configuration du backup."""
    _check_backup_permission(db, current_user)

    update_fields = data.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="Aucun champ a mettre a jour")

    config = upsert_backup_config(db, **update_fields)
    log_action(db, current_user.id, "update", "backup_config", config.id)

    return _config_to_response(config, db)


# ════════════════════════════════════════════════════════════════
# OAUTH ENDPOINTS
# ════════════════════════════════════════════════════════════════

@router.post("/config/oauth/url", response_model=OAuthUrlResponse)
def get_oauth_url(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Genere l'URL de redirection Google OAuth."""
    _check_backup_permission(db, current_user)

    auth_url, state = build_google_auth_url(current_user.id)
    return OAuthUrlResponse(redirect_url=auth_url, state=state)


@router.get("/config/oauth/callback")
def oauth_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
):
    """
    Callback OAuth Google (navigateur redirect, pas de JWT).
    Redirige vers le frontend apres traitement.
    """
    frontend_url = settings.FRONTEND_URL
    redirect_base = f"{frontend_url}/settings?tab=admin&section=sauvegardes"

    if error:
        logger.warning(f"OAuth Google erreur: {error}")
        return RedirectResponse(url=f"{redirect_base}&oauth=error&detail={error}")

    if not code or not state:
        return RedirectResponse(url=f"{redirect_base}&oauth=error&detail=missing_params")

    try:
        # Verifier le state (protection CSRF)
        payload = verify_google_state(state)
        user_id = payload["user_id"]

        # Echanger le code contre des tokens
        token_data = exchange_google_code(code)

        if not token_data["access_token"]:
            return RedirectResponse(url=f"{redirect_base}&oauth=error&detail=no_token")

        # Sauvegarder dans la base
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=token_data["expires_in"])

            upsert_backup_config(
                db,
                google_access_token=encrypt_totp_secret(token_data["access_token"]),
                google_refresh_token=(
                    encrypt_totp_secret(token_data["refresh_token"])
                    if token_data["refresh_token"] else None
                ),
                google_token_expires_at=expires_at,
                google_email=token_data["email"],
                is_connected=True,
                connected_by=user_id,
                connected_at=now,
            )

            log_action(db, user_id, "oauth_connect", "backup_config", 0)

            # Auto-creation du dossier par defaut si aucun n'est configure
            try:
                cfg = get_backup_config(db)
                if not cfg.google_drive_folder_id:
                    default_name = "RadioManager-Backups"
                    # Chercher un dossier existant avant d'en creer un nouveau
                    existing_folders = list_drive_folders(token_data["access_token"])
                    existing = next((f for f in existing_folders if f.get("name") == default_name), None)

                    if existing:
                        # Reutiliser le dossier existant
                        upsert_backup_config(
                            db,
                            google_drive_folder_id=existing["id"],
                            google_drive_folder_name=default_name,
                        )
                        logger.info(f"Dossier Drive existant reutilise: {existing['id']}")
                    else:
                        # Creer un nouveau dossier
                        folder_result = create_drive_folder(
                            token_data["access_token"],
                            default_name
                        )
                        if folder_result.get("id"):
                            upsert_backup_config(
                                db,
                                google_drive_folder_id=folder_result["id"],
                                google_drive_folder_name=default_name,
                            )
                            logger.info(f"Dossier Drive auto-cree: {folder_result['id']}")
            except Exception as e:
                logger.warning(f"Impossible de creer le dossier par defaut: {e}")
                # Non-bloquant : la connexion reste valide

        finally:
            db.close()

        return RedirectResponse(url=f"{redirect_base}&oauth=success")

    except HTTPException as e:
        logger.error(f"OAuth callback error: {e.detail}")
        return RedirectResponse(url=f"{redirect_base}&oauth=error&detail=invalid_state")
    except Exception as e:
        logger.error(f"OAuth callback unexpected error: {e}")
        return RedirectResponse(url=f"{redirect_base}&oauth=error&detail=server_error")


@router.post("/config/disconnect")
def disconnect_google_drive(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deconnecte Google Drive."""
    _check_backup_permission(db, current_user)

    upsert_backup_config(
        db,
        google_access_token=None,
        google_refresh_token=None,
        google_token_expires_at=None,
        google_email=None,
        is_connected=False,
        connected_by=None,
        connected_at=None,
    )

    log_action(db, current_user.id, "oauth_disconnect", "backup_config", 0)
    return {"message": "Google Drive deconnecte"}


# ════════════════════════════════════════════════════════════════
# BACKUP TRIGGER
# ════════════════════════════════════════════════════════════════

@router.post("/trigger", response_model=BackupTriggerResponse)
def trigger_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Declenche un backup manuel en arriere-plan."""
    _check_backup_permission(db, current_user)

    config = get_backup_config(db)
    if not config or not config.is_connected:
        raise HTTPException(
            status_code=400,
            detail="Google Drive non connecte. Configurez d'abord la connexion."
        )

    # Trouver le fichier de backup le plus recent
    backup_files = sorted(
        glob.glob(os.path.join(BACKUP_DIR, "dump_*.sql.gz")),
        key=os.path.getmtime,
        reverse=True,
    )
    if not backup_files:
        raise HTTPException(
            status_code=404,
            detail="Aucun fichier de backup trouve dans /backups. Verifiez le cron pg_dumpall."
        )

    latest_file = backup_files[0]
    filename = os.path.basename(latest_file)

    # Creer l'entree d'historique
    history = create_backup_history(db, filename=filename, backup_type="manual", triggered_by=current_user.id)

    # Creer la tache
    task_id = sync_tasks.create(label=f"backup-{filename}")

    # Lancer le backup en arriere-plan
    def _run_backup():
        session = SessionLocal()
        try:
            sync_tasks.update(task_id, progress="Verification du token Google...", percent=10)

            access_token = ensure_valid_token(session)
            if not access_token:
                sync_tasks.fail(task_id, "Token Google invalide ou expire")
                update_backup_history(session, history.id, status="failed", error_message="Token Google invalide")
                return

            sync_tasks.update(task_id, progress=f"Upload de {filename} vers Google Drive...", percent=30)

            cfg = get_backup_config(session)
            folder_id = cfg.google_drive_folder_id if cfg else None

            result = upload_to_drive(access_token, folder_id, latest_file, filename)

            sync_tasks.update(task_id, progress="Mise a jour de l'historique...", percent=90)

            file_size = os.path.getsize(latest_file)
            now = datetime.now(timezone.utc)
            started = history.started_at or now
            duration = int((now - started).total_seconds())

            update_backup_history(
                session,
                history.id,
                status="completed",
                file_size_bytes=file_size,
                google_drive_file_id=result.get("id"),
                uploaded_to_drive=True,
                completed_at=now,
                duration_seconds=duration,
            )

            log_action(session, current_user.id, "backup_complete", "backup_history", history.id)
            sync_tasks.complete(task_id, {"backup_id": history.id, "drive_file_id": result.get("id")})

        except Exception as e:
            logger.error(f"Erreur backup: {e}")
            sync_tasks.fail(task_id, str(e))
            try:
                update_backup_history(session, history.id, status="failed", error_message=str(e)[:500])
            except Exception:
                pass
        finally:
            session.close()

    thread = threading.Thread(target=_run_backup, daemon=True)
    thread.start()

    log_action(db, current_user.id, "backup_trigger", "backup_history", history.id)

    return BackupTriggerResponse(
        task_id=task_id,
        backup_id=history.id,
        message=f"Backup de {filename} lance en arriere-plan",
    )


# ════════════════════════════════════════════════════════════════
# STATUS / HISTORY / FILES
# ════════════════════════════════════════════════════════════════

@router.get("/status/{task_id}")
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le statut d'une tache de backup/restore."""
    _check_backup_permission(db, current_user)

    task = sync_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tache introuvable")
    return task


@router.get("/history", response_model=BackupHistoryPaginated)
def list_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne l'historique pagine des backups.

    Synchronise automatiquement les fichiers Google Drive non presents
    dans l'historique local (utile apres reinstallation du VPS).
    """
    _check_backup_permission(db, current_user)

    # Sync Drive → DB : importer les fichiers Drive non connus localement
    _sync_drive_to_history(db)

    items, total = get_backup_history(db, skip=skip, limit=limit)
    return BackupHistoryPaginated(
        total=total,
        items=[BackupHistoryResponse.model_validate(item) for item in items],
        skip=skip,
        limit=limit,
    )


@router.get("/files", response_model=list[BackupFileInfo])
def list_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liste les fichiers de backup disponibles (local + Drive)."""
    _check_backup_permission(db, current_user)

    files: list[BackupFileInfo] = []

    # Fichiers locaux
    if os.path.isdir(BACKUP_DIR):
        for filepath in sorted(glob.glob(os.path.join(BACKUP_DIR, "dump_*.sql.gz")), reverse=True):
            stat = os.stat(filepath)
            files.append(BackupFileInfo(
                filename=os.path.basename(filepath),
                size_bytes=stat.st_size,
                source="local",
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            ))

    # Fichiers sur Google Drive
    config = get_backup_config(db)
    if config and config.is_connected and config.google_drive_folder_id:
        access_token = ensure_valid_token(db)
        if access_token:
            drive_files = list_drive_files(access_token, config.google_drive_folder_id)
            local_filenames = {f.filename for f in files}
            for df in drive_files:
                if df.get("name") not in local_filenames:
                    modified = None
                    if df.get("modifiedTime"):
                        try:
                            modified = datetime.fromisoformat(df["modifiedTime"].replace("Z", "+00:00"))
                        except Exception:
                            pass
                    files.append(BackupFileInfo(
                        filename=df.get("name", "unknown"),
                        size_bytes=int(df["size"]) if df.get("size") else None,
                        source="drive",
                        google_drive_file_id=df.get("id"),
                        modified_at=modified,
                    ))

    return files


# ════════════════════════════════════════════════════════════════
# RESTORE
# ════════════════════════════════════════════════════════════════

# IMPORTANT: /restore/upload DOIT etre declare AVANT /restore/{backup_id}
# sinon FastAPI interprete "upload" comme un backup_id entier

MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 Mo

@router.post("/restore/upload", response_model=BackupRestoreResponse)
def restore_from_upload(
    file: UploadFile = File(...),
    confirm: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Restaure la base depuis un fichier .sql.gz uploade.
    Necessite confirm='RESTAURER' dans le body.
    """
    _check_backup_permission(db, current_user)

    if confirm != "RESTAURER":
        raise HTTPException(
            status_code=400,
            detail="Pour confirmer la restauration, envoyez confirm='RESTAURER'"
        )

    if not file.filename or not file.filename.endswith(".sql.gz"):
        raise HTTPException(status_code=400, detail="Le fichier doit etre au format .sql.gz")

    # Sauvegarder le fichier uploade
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = f"upload_{timestamp}_{file.filename}"
    filepath = os.path.join(BACKUP_DIR, safe_name)

    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        total_size = 0
        with open(filepath, "wb") as f:
            while True:
                chunk = file.file.read(8192)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE:
                    f.close()
                    os.remove(filepath)
                    raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 500 Mo)")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur sauvegarde fichier upload: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du fichier")

    task_id = sync_tasks.create(label=f"restore-upload-{safe_name}")

    def _run_upload_restore():
        session = SessionLocal()
        try:
            sync_tasks.update(task_id, progress="Nettoyage du schema avant restauration...", percent=10)

            # Vider le schema public pour eviter les conflits (tables existantes, PK dupliquees)
            drop_result = subprocess.run(
                'PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOSTNAME -U $DATABASE_USERNAME -d $DATABASE_NAME '
                '-c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if drop_result.returncode != 0:
                error_msg = drop_result.stderr[:500] if drop_result.stderr else "Erreur inconnue"
                logger.error(f"Erreur DROP SCHEMA: {error_msg}")
                sync_tasks.fail(task_id, f"Echec nettoyage schema: {error_msg}")
                return

            sync_tasks.update(task_id, progress="Restauration de la base de donnees...", percent=30)

            result = subprocess.run(
                f"gunzip -c {filepath} | PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOSTNAME -U $DATABASE_USERNAME -d $DATABASE_NAME",
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,
            )

            # psql retourne 0 meme avec des erreurs non fatales (CREATE ROLE, CREATE DATABASE)
            # On verifie stderr pour les erreurs critiques (hors role/database qui sont attendues)
            stderr = result.stderr or ""
            critical_errors = [
                line for line in stderr.splitlines()
                if "ERROR:" in line
                and "already exists" not in line
                and "role" not in line.lower()
                and "database" not in line.lower()
            ]

            if result.returncode != 0 and critical_errors:
                error_msg = "\n".join(critical_errors[:5])
                logger.error(f"Erreurs critiques restauration: {error_msg}")
                sync_tasks.fail(task_id, f"psql erreur: {error_msg}")
                return

            if critical_errors:
                logger.warning(f"Restauration terminee avec avertissements: {len(critical_errors)} erreurs")

            # Resynchroniser toutes les sequences auto-increment apres restauration
            sync_tasks.update(task_id, progress="Resynchronisation des sequences...", percent=90)
            subprocess.run(
                "PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOSTNAME -U $DATABASE_USERNAME -d $DATABASE_NAME -c \""
                "DO \\$\\$ DECLARE r RECORD; BEGIN "
                "FOR r IN (SELECT sequencename, tablename, columnname FROM pg_sequences ps "
                "JOIN information_schema.columns c ON c.column_default LIKE '%' || ps.sequencename || '%' "
                "WHERE ps.schemaname = 'public') LOOP "
                "EXECUTE format('SELECT setval(''%I'', COALESCE(MAX(%I), 1)) FROM %I', r.sequencename, r.columnname, r.tablename); "
                "END LOOP; END \\$\\$;\"",
                shell=True, capture_output=True, text=True, timeout=30,
            )

            log_action(session, current_user.id, "restore_upload_complete", "backup_history", 0)
            sync_tasks.complete(task_id, {"filename": safe_name})

        except subprocess.TimeoutExpired:
            sync_tasks.fail(task_id, "Timeout: la restauration a depasse 10 minutes")
        except Exception as e:
            logger.error(f"Erreur restauration upload: {e}")
            sync_tasks.fail(task_id, str(e))
        finally:
            # Nettoyage du fichier uploade
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass
            session.close()

    thread = threading.Thread(target=_run_upload_restore, daemon=True)
    thread.start()

    log_action(db, current_user.id, "restore_upload_trigger", "backup_history", 0)

    return BackupRestoreResponse(
        task_id=task_id,
        message=f"Restauration depuis {file.filename} lancee en arriere-plan",
    )


@router.post("/restore/{backup_id}", response_model=BackupRestoreResponse)
def trigger_restore(
    backup_id: int,
    body: BackupRestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Declenche une restauration depuis un backup.
    Necessite confirm='RESTAURER' dans le body.
    """
    logger.info(f"[RESTORE] Requete restauration backup_id={backup_id} par user={current_user.id} ({current_user.email})")
    _check_backup_permission(db, current_user)

    if body.confirm != "RESTAURER":
        raise HTTPException(
            status_code=400,
            detail="Pour confirmer la restauration, envoyez confirm='RESTAURER'"
        )

    backup = get_backup_by_id(db, backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup introuvable")

    if backup.status != "completed":
        raise HTTPException(status_code=400, detail="Seuls les backups termines peuvent etre restaures")

    task_id = sync_tasks.create(label=f"restore-{backup.filename}")

    def _run_restore():
        session = SessionLocal()
        try:
            logger.info(f"[RESTORE] Demarrage restauration backup_id={backup_id} filename={backup.filename}")
            sync_tasks.update(task_id, progress="Preparation de la restauration...", percent=10)

            # S'assurer que le repertoire de backup existe
            os.makedirs(BACKUP_DIR, exist_ok=True)

            filepath = os.path.join(BACKUP_DIR, backup.filename)
            logger.info(f"[RESTORE] Fichier cible: {filepath}, existe={os.path.exists(filepath)}, drive_id={backup.google_drive_file_id}")

            # Telecharger depuis Drive si le fichier n'est pas en local
            if not os.path.exists(filepath) and backup.google_drive_file_id:
                sync_tasks.update(task_id, progress="Telechargement depuis Google Drive...", percent=20)
                logger.info(f"[RESTORE] Telechargement depuis Drive: {backup.google_drive_file_id}")
                access_token = ensure_valid_token(session)
                if not access_token:
                    logger.error("[RESTORE] Token Google invalide ou impossible a rafraichir")
                    sync_tasks.fail(task_id, "Token Google invalide")
                    return
                try:
                    download_from_drive(access_token, backup.google_drive_file_id, filepath)
                    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                    logger.info(f"[RESTORE] Telechargement OK: {filepath} ({file_size} bytes)")
                except Exception as dl_err:
                    logger.error(f"[RESTORE] Echec telechargement Drive: {dl_err}")
                    sync_tasks.fail(task_id, f"Erreur telechargement Drive: {dl_err}")
                    return

            if not os.path.exists(filepath):
                logger.error(f"[RESTORE] Fichier introuvable apres tentative: {filepath}")
                sync_tasks.fail(task_id, f"Fichier {backup.filename} introuvable")
                return

            logger.info(f"[RESTORE] Fichier pret: {filepath} ({os.path.getsize(filepath)} bytes)")
            sync_tasks.update(task_id, progress="Nettoyage du schema avant restauration...", percent=40)

            # Vider le schema public pour eviter les conflits (tables existantes, PK dupliquees)
            drop_result = subprocess.run(
                'PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOSTNAME -U $DATABASE_USERNAME -d $DATABASE_NAME '
                '-c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if drop_result.returncode != 0:
                error_msg = drop_result.stderr[:500] if drop_result.stderr else "Erreur inconnue"
                logger.error(f"[RESTORE] Erreur DROP SCHEMA (rc={drop_result.returncode}): {error_msg}")
                sync_tasks.fail(task_id, f"Echec nettoyage schema: {error_msg}")
                return

            logger.info("[RESTORE] DROP SCHEMA OK, lancement psql restore...")
            sync_tasks.update(task_id, progress="Restauration de la base de donnees...", percent=50)

            result = subprocess.run(
                f"gunzip -c {filepath} | PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOSTNAME -U $DATABASE_USERNAME -d $DATABASE_NAME",
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,
            )

            logger.info(f"[RESTORE] psql termine rc={result.returncode}, stderr_len={len(result.stderr or '')}")

            # psql retourne 0 meme avec des erreurs non fatales (CREATE ROLE, CREATE DATABASE)
            stderr = result.stderr or ""
            critical_errors = [
                line for line in stderr.splitlines()
                if "ERROR:" in line
                and "already exists" not in line
                and "role" not in line.lower()
                and "database" not in line.lower()
            ]

            if result.returncode != 0 and critical_errors:
                error_msg = "\n".join(critical_errors[:5])
                logger.error(f"[RESTORE] Erreurs critiques psql: {error_msg}")
                sync_tasks.fail(task_id, f"psql erreur: {error_msg}")
                return

            if critical_errors:
                logger.warning(f"[RESTORE] Restauration avec avertissements: {len(critical_errors)} erreurs non-critiques")

            # Resynchroniser toutes les sequences auto-increment apres restauration
            logger.info("[RESTORE] Resynchronisation des sequences...")
            sync_tasks.update(task_id, progress="Resynchronisation des sequences...", percent=90)
            subprocess.run(
                "PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOSTNAME -U $DATABASE_USERNAME -d $DATABASE_NAME -c \""
                "DO \\$\\$ DECLARE r RECORD; BEGIN "
                "FOR r IN (SELECT sequencename, tablename, columnname FROM pg_sequences ps "
                "JOIN information_schema.columns c ON c.column_default LIKE '%' || ps.sequencename || '%' "
                "WHERE ps.schemaname = 'public') LOOP "
                "EXECUTE format('SELECT setval(''%I'', COALESCE(MAX(%I), 1)) FROM %I', r.sequencename, r.columnname, r.tablename); "
                "END LOOP; END \\$\\$;\"",
                shell=True, capture_output=True, text=True, timeout=30,
            )

            logger.info(f"[RESTORE] Restauration terminee avec succes: {backup.filename}")
            log_action(session, current_user.id, "restore_complete", "backup_history", backup_id)
            sync_tasks.complete(task_id, {"backup_id": backup_id, "filename": backup.filename})

        except subprocess.TimeoutExpired:
            logger.error(f"[RESTORE] Timeout depassé pour {backup.filename}")
            sync_tasks.fail(task_id, "Timeout: la restauration a depasse 10 minutes")
        except Exception as e:
            logger.error(f"[RESTORE] Exception inattendue: {e}", exc_info=True)
            sync_tasks.fail(task_id, str(e))
        finally:
            session.close()

    thread = threading.Thread(target=_run_restore, daemon=True)
    thread.start()

    log_action(db, current_user.id, "restore_trigger", "backup_history", backup_id)

    return BackupRestoreResponse(
        task_id=task_id,
        message=f"Restauration de {backup.filename} lancee en arriere-plan",
    )


# ════════════════════════════════════════════════════════════════
# DRIVE FOLDERS
# ════════════════════════════════════════════════════════════════

@router.get("/drive/folders", response_model=list[DriveFolderInfo])
def get_drive_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liste les dossiers Google Drive crees par l'application."""
    _check_backup_permission(db, current_user)

    access_token = ensure_valid_token(db)
    if not access_token:
        raise HTTPException(status_code=400, detail="Token Google invalide ou expire")

    folders = list_drive_folders(access_token)
    return [DriveFolderInfo(id=f["id"], name=f["name"]) for f in folders if f.get("id")]


@router.post("/drive/folders", response_model=DriveFolderInfo)
def create_folder(
    body: CreateFolderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cree un nouveau dossier dans Google Drive."""
    _check_backup_permission(db, current_user)

    access_token = ensure_valid_token(db)
    if not access_token:
        raise HTTPException(status_code=400, detail="Token Google invalide ou expire")

    result = create_drive_folder(access_token, body.folder_name)
    if not result.get("id"):
        raise HTTPException(status_code=502, detail="Echec de la creation du dossier Drive")

    log_action(db, current_user.id, "create", "drive_folder", 0)
    return DriveFolderInfo(id=result["id"], name=result["name"])
