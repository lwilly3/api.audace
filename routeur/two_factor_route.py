"""
Routes API pour la gestion du 2FA (TOTP).

Prefixe : /auth/2fa
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

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
    regenerate_backup_codes,
)
from app.db.crud.crud_permissions import get_user_permissions
from core.auth.oauth2 import create_acces_token
from app.db.crud.crud_audit_logs import log_action


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

class BackupCodeLoginRequest(BaseModel):
    temp_token: str
    backup_code: str


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
def two_factor_verify_login(
    request: VerifyLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Verifie le code OTP pendant le login (2eme etape).
    Accepte un temp_token (JWT 5min avec purpose=2fa_verify).
    Retourne le token complet + permissions si valide.
    """
    # Valider le temp token et extraire le user_id
    user_data = get_2fa_temp_user(request.temp_token, db)

    # Verifier le code OTP
    if not verify_totp(db, user_data.id, request.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code OTP invalide"
        )

    # Generer le token complet
    return _build_login_response(db, user_data)


@router.post('/verify-backup')
def two_factor_verify_backup(
    request: BackupCodeLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Verifie un code de secours pendant le login (alternative au TOTP).
    """
    user_data = get_2fa_temp_user(request.temp_token, db)

    if not verify_and_consume_backup_code(db, user_data.id, request.backup_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code de secours invalide"
        )

    log_action(db, user_data.id, "2fa_backup_code_used", "users", user_data.id)
    return _build_login_response(db, user_data)


# --- Endpoint admin ---

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
