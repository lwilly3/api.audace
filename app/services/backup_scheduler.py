"""
Planificateur de sauvegardes automatiques.

Execute un pg_dump quotidien + upload Google Drive selon la configuration
stockee en base (backup_config.auto_backup_enabled, auto_backup_hour).

Le scheduler tourne dans un thread daemon, verifie toutes les 60 secondes
si l'heure programmee est atteinte, et utilise get_today_backup() pour
eviter les doublons.

Partage entre workers : un fichier lock (/app/data/backup_scheduler.lock)
garantit qu'un seul worker a la main. Les autres workers ne lancent pas
le thread scheduler.

L'heure configuree (auto_backup_hour) est interprete en heure locale
Africa/Douala (UTC+1). Le scheduler la convertit en UTC pour comparer.

Usage :
    from app.services.backup_scheduler import backup_scheduler
    backup_scheduler.start()    # dans lifespan startup
    backup_scheduler.stop()     # dans lifespan shutdown
"""

import fcntl
import glob
import gzip
import logging
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config.config import settings

logger = logging.getLogger("backup-scheduler")

BACKUP_DIR = "/backups"
LOCK_FILE = "/app/data/backup_scheduler.lock"

# Fuseau horaire local (Africa/Douala = UTC+1)
LOCAL_UTC_OFFSET_HOURS = 1


class BackupScheduler:
    """Planificateur de sauvegardes automatiques quotidiennes."""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_check_date: Optional[str] = None
        self._last_result: Optional[dict] = None
        self._lock_fd = None

    # ── Lifecycle ───────────────────────

    def _acquire_lock(self) -> bool:
        """Tente d'acquerir le fichier lock (un seul worker parmi les 4 de Gunicorn)."""
        try:
            os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
            self._lock_fd = open(LOCK_FILE, 'w')
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_fd.write(f"{os.getpid()}\n")
            self._lock_fd.flush()
            return True
        except (IOError, OSError):
            # Un autre worker a deja le lock
            if self._lock_fd:
                self._lock_fd.close()
                self._lock_fd = None
            return False

    def _release_lock(self):
        """Libere le fichier lock."""
        if self._lock_fd:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                self._lock_fd.close()
            except Exception:
                pass
            self._lock_fd = None

    def start(self):
        """Demarrer le scheduler en arriere-plan (un seul worker via flock)."""
        if self._running:
            return
        if not self._acquire_lock():
            logger.info("Backup scheduler: un autre worker a le lock, skip")
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="backup-scheduler")
        self._thread.start()
        logger.info(f"Backup scheduler demarre (PID={os.getpid()})")

    def stop(self):
        """Arreter le scheduler proprement."""
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._release_lock()
        logger.info("Backup scheduler arrete")

    def get_status(self) -> dict:
        """Retourne le statut du scheduler."""
        now_utc = datetime.now(timezone.utc)
        local_hour = (now_utc + timedelta(hours=LOCAL_UTC_OFFSET_HOURS)).hour
        return {
            "running": self._running,
            "pid": os.getpid(),
            "utc_hour": now_utc.hour,
            "local_hour": local_hour,
            "local_offset": f"UTC+{LOCAL_UTC_OFFSET_HOURS}",
            "last_check_date": self._last_check_date,
            "last_result": self._last_result,
        }

    # ── Main loop ───────────────────────

    def _loop(self):
        """Boucle principale : verifie toutes les 60 secondes."""
        while not self._stop_event.is_set():
            try:
                self._check_and_run()
            except Exception as e:
                logger.error(f"Erreur dans la boucle backup scheduler: {e}")
            # Dormir 60 secondes entre chaque verification
            self._stop_event.wait(timeout=60)

    def _check_and_run(self):
        """Verifie si un backup automatique doit etre lance."""
        from app.db.database import SessionLocal
        from app.db.crud.crud_backup import get_backup_config, get_today_backup

        session = SessionLocal()
        try:
            config = get_backup_config(session)
            if not config:
                return
            if not config.auto_backup_enabled:
                return
            if not config.is_connected:
                return

            now_utc = datetime.now(timezone.utc)
            # Convertir en heure locale (Africa/Douala = UTC+1)
            local_time = now_utc + timedelta(hours=LOCAL_UTC_OFFSET_HOURS)
            current_local_hour = local_time.hour
            target_hour = config.auto_backup_hour or 3

            # Verifier si c'est l'heure programmee (en heure locale)
            if current_local_hour != target_hour:
                return

            # Deduplication : verifier si un backup scheduled a deja ete fait aujourd'hui
            existing = get_today_backup(session)
            if existing:
                return

            self._last_check_date = now_utc.isoformat()
            logger.info(f"Backup automatique declenche (heure locale={target_hour}h, UTC={now_utc.hour}h)")
            self._run_backup(session, config)

        except Exception as e:
            logger.error(f"Erreur verification backup: {e}")
            self._last_result = {"status": "error", "message": str(e), "at": datetime.now(timezone.utc).isoformat()}
        finally:
            session.close()

    def _run_backup(self, session, config):
        """Execute le pg_dump + upload vers Google Drive."""
        from app.db.crud.crud_backup import create_backup_history, update_backup_history
        from app.services.google_drive_client import ensure_valid_token, upload_to_drive

        # Etape 1 : pg_dump
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"dump_{timestamp}.sql.gz"
        filepath = os.path.join(BACKUP_DIR, filename)

        os.makedirs(BACKUP_DIR, exist_ok=True)

        try:
            logger.info(f"pg_dump en cours...")
            result = subprocess.run(
                [
                    "pg_dump",
                    "-h", settings.DATABASE_HOSTNAME,
                    "-p", settings.DATABASE_PORT,
                    "-U", settings.DATABASE_USERNAME,
                    "-d", settings.DATABASE_NAME,
                    "--no-password",
                ],
                capture_output=True,
                timeout=300,
                env={**os.environ, "PGPASSWORD": settings.DATABASE_PASSWORD},
            )

            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='replace')[:500]
                logger.error(f"pg_dump echoue: {error_msg}")
                self._last_result = {"status": "error", "message": f"pg_dump echoue: {error_msg}", "at": datetime.now(timezone.utc).isoformat()}
                return

            # Compresser en gzip
            with gzip.open(filepath, 'wb') as f:
                f.write(result.stdout)

            file_size = os.path.getsize(filepath)
            logger.info(f"pg_dump OK: {filename} ({file_size} bytes)")

        except subprocess.TimeoutExpired:
            logger.error("pg_dump timeout (>5min)")
            self._last_result = {"status": "error", "message": "pg_dump timeout", "at": datetime.now(timezone.utc).isoformat()}
            return
        except Exception as e:
            logger.error(f"pg_dump exception: {e}")
            self._last_result = {"status": "error", "message": str(e), "at": datetime.now(timezone.utc).isoformat()}
            return

        # Etape 2 : creer l'entree d'historique
        history = create_backup_history(session, filename=filename, backup_type="scheduled")

        # Etape 3 : upload vers Google Drive
        try:
            access_token = ensure_valid_token(session)
            if not access_token:
                update_backup_history(session, history.id, status="failed", error_message="Token Google invalide ou expire")
                self._last_result = {"status": "error", "message": "Token Google invalide", "at": datetime.now(timezone.utc).isoformat()}
                return

            folder_id = config.google_drive_folder_id
            drive_result = upload_to_drive(access_token, folder_id, filepath, filename)

            now = datetime.now(timezone.utc)
            started = history.started_at or now
            duration = int((now - started).total_seconds())

            update_backup_history(
                session,
                history.id,
                status="completed",
                file_size_bytes=file_size,
                google_drive_file_id=drive_result.get("id"),
                uploaded_to_drive=True,
                completed_at=now,
                duration_seconds=duration,
            )

            self._last_result = {
                "status": "completed",
                "filename": filename,
                "file_size": file_size,
                "drive_file_id": drive_result.get("id"),
                "at": now.isoformat(),
            }
            logger.info(f"Backup automatique termine: {filename} -> Google Drive ({drive_result.get('id')})")

        except Exception as e:
            logger.error(f"Upload Google Drive echoue: {e}")
            update_backup_history(session, history.id, status="failed", error_message=str(e)[:500])
            self._last_result = {"status": "error", "message": str(e), "at": datetime.now(timezone.utc).isoformat()}

        # Etape 4 : nettoyage des vieux dumps (retention)
        try:
            retention_days = config.retention_days or 30
            self._cleanup_old_dumps(retention_days)
        except Exception as e:
            logger.warning(f"Nettoyage vieux dumps echoue: {e}")

    def _cleanup_old_dumps(self, retention_days: int):
        """Supprime les fichiers dump plus vieux que retention_days."""
        cutoff = time.time() - (retention_days * 86400)
        removed = 0
        for filepath in glob.glob(os.path.join(BACKUP_DIR, "dump_*.sql.gz")):
            try:
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
                    removed += 1
            except OSError:
                pass
        if removed:
            logger.info(f"Nettoyage: {removed} ancien(s) dump(s) supprime(s) (retention={retention_days}j)")


# Singleton global
backup_scheduler = BackupScheduler()
