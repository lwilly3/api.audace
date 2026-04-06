"""
Routes API pour la gestion du 2FA (TOTP).

Prefixe : /auth/2fa
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.db.database import get_db
from app.models.model_user import User
from app.models.model_user_permissions import UserPermissions
from core.auth.oauth2 import get_current_user, get_2fa_temp_user
from app.db.crud.crud_2fa import (
    setup_totp,
    confirm_totp_setup,
    verify_totp,
    verify_and_consume_backup_code,
    disable_totp,
    admin_reset_totp,
    admin_reset_all_totp,
    get_users_with_2fa,
    regenerate_backup_codes,
    create_trusted_device,
)
from app.db.crud.crud_permissions import get_user_permissions
from core.auth.oauth2 import create_acces_token
from app.db.crud.crud_audit_logs import log_action
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


router = APIRouter(
    prefix='/auth/2fa',
    tags=['Two-Factor Authentication']
)


# --- Schemas Pydantic ---

class OTPRequest(BaseModel):
    otp_code: str

class VerifyLoginRequest(BaseModel):
    temp_token: str
    otp_code: str
    trust_browser: Optional[bool] = False

class BackupCodeLoginRequest(BaseModel):
    temp_token: str
    backup_code: str
    trust_browser: Optional[bool] = False

class ResetAll2FARequest(BaseModel):
    user_ids: Optional[List[int]] = None


# --- Endpoints authentifies (Bearer token complet) ---

@router.post('/setup')
def two_factor_setup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Genere un secret TOTP + QR code pour le setup initial."""
    result = setup_totp(db, current_user.id)
    return result


@router.post('/verify-setup')
def two_factor_verify_setup(
    request: OTPRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verifie le premier code OTP pour activer le 2FA. Retourne les backup codes."""
    result = confirm_totp_setup(db, current_user.id, request.otp_code)
    log_action(db, current_user.id, "2fa_enabled", "users", current_user.id)
    return result


@router.post('/disable')
def two_factor_disable(
    request: OTPRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Desactive le 2FA (requiert un code OTP valide)."""
    # Verifier si un role de l'utilisateur exige le 2FA
    for role in current_user.roles:
        if role.require_2fa or role.name == 'super_admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre role exige l'activation du 2FA. Vous ne pouvez pas le desactiver."
            )
    disable_totp(db, current_user.id, request.otp_code)
    log_action(db, current_user.id, "2fa_disabled", "users", current_user.id)
    return {"message": "2FA desactive avec succes"}


@router.post('/backup-codes/regenerate')
def two_factor_regenerate_backup_codes(
    request: OTPRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenere les codes de secours (requiert un code OTP valide)."""
    result = regenerate_backup_codes(db, current_user.id, request.otp_code)
    log_action(db, current_user.id, "2fa_backup_codes_regenerated", "users", current_user.id)
    return result


# --- Endpoint verification login (temp token) ---

@router.post('/verify')
@limiter.limit("5/minute")
def two_factor_verify_login(
    request: Request,
    payload: VerifyLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Verifie le code OTP pendant le login (2eme etape).
    Accepte un temp_token (JWT 5min avec purpose=2fa_verify).
    Retourne le token complet + permissions si valide.
    Si trust_browser=True, genere un device token pour les connexions futures.
    """
    # Valider le temp token et extraire le user_id
    user_data = get_2fa_temp_user(payload.temp_token, db)

    # Verifier le code OTP
    if not verify_totp(db, user_data.id, payload.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code OTP invalide"
        )

    # Generer le token complet
    response = _build_login_response(db, user_data)

    # Si trust_browser, generer un device token
    if payload.trust_browser:
        user_agent = request.headers.get("User-Agent", "")
        device_token = create_trusted_device(db, user_data.id, user_agent)
        response["trusted_device_token"] = device_token
        log_action(db, user_data.id, "trusted_device_created", "users", user_data.id)

    return response


@router.post('/verify-backup')
@limiter.limit("3/minute")
def two_factor_verify_backup(
    request: Request,
    payload: BackupCodeLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Verifie un code de secours pendant le login (alternative au TOTP).
    """
    user_data = get_2fa_temp_user(payload.temp_token, db)

    if not verify_and_consume_backup_code(db, user_data.id, payload.backup_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code de secours invalide"
        )

    log_action(db, user_data.id, "2fa_backup_code_used", "users", user_data.id)
    response = _build_login_response(db, user_data)

    # Si trust_browser, generer un device token
    if payload.trust_browser:
        user_agent = request.headers.get("User-Agent", "")
        device_token = create_trusted_device(db, user_data.id, user_agent)
        response["trusted_device_token"] = device_token
        log_action(db, user_data.id, "trusted_device_created", "users", user_data.id)

    return response


# --- Endpoint admin ---

@router.get('/admin/users-2fa')
def list_users_with_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste les utilisateurs avec 2FA actif (pour selection avant reset)."""
    is_super_admin = any(r.name == 'super_admin' for r in current_user.roles)
    if not is_super_admin:
        perms = db.query(UserPermissions).filter(UserPermissions.user_id == current_user.id).first()
        if not perms or not perms.can_reset_user_2fa:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission can_reset_user_2fa requise"
            )
    return get_users_with_2fa(db)


@router.post('/admin/reset-all')
def two_factor_admin_reset_all(
    body: ResetAll2FARequest = ResetAll2FARequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset le 2FA des utilisateurs (tous ou selection). Body optionnel: {user_ids: [1,2,3]}."""
    is_super_admin = any(r.name == 'super_admin' for r in current_user.roles)
    if not is_super_admin:
        perms = db.query(UserPermissions).filter(UserPermissions.user_id == current_user.id).first()
        if not perms or not perms.can_reset_user_2fa:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission can_reset_user_2fa requise"
            )

    affected = admin_reset_all_totp(db, user_ids=body.user_ids)
    log_action(db, current_user.id, "2fa_admin_reset_all", "users", 0)
    return {
        "message": f"2FA reinitialise pour {affected} utilisateur(s)",
        "affected_count": affected,
    }


@router.post('/admin/reset/{user_id}')
def two_factor_admin_reset(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset le 2FA d'un utilisateur (admin uniquement)."""
    # Verifier la permission
    perms = db.query(UserPermissions).filter(UserPermissions.user_id == current_user.id).first()
    if not perms or not perms.can_reset_user_2fa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission can_reset_user_2fa requise"
        )

    admin_reset_totp(db, user_id)
    log_action(db, current_user.id, "2fa_admin_reset", "users", user_id)
    return {"message": "2FA reinitialise avec succes"}


# --- Helper ---

def _build_login_response(db: Session, user: User) -> dict:
    """Construit la reponse de login complete (identique a /auth/login)."""
    access_token = create_acces_token(data={'user_id': user.id})
    permissions = get_user_permissions(db, user.id)
    log_action(db, user.id, "login_2fa", "users", user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "family_name": user.family_name,
        "name": user.name,
        "phone_number": user.phone_number,
        "profilePicture": user.profilePicture,
        "permissions": permissions,
    }
