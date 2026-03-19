"""
CRUD pour la gestion du 2FA (TOTP) et des appareils de confiance.

Operations : setup, confirm, verify, disable, admin reset, backup codes, trusted devices.
"""

import io
import uuid
import hashlib
import base64
import pyotp
import qrcode
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.model_user import User
from app.models.model_trusted_device import TrustedDevice
from app.utils.crypto import (
    encrypt_totp_secret,
    decrypt_totp_secret,
    generate_backup_codes,
    hash_backup_codes,
    verify_backup_code,
)


# Nom affiche dans l'app TOTP (Google Authenticator, Authy, etc.)
TOTP_ISSUER = "RadioManager"


def setup_totp(db: Session, user_id: int) -> dict:
    """
    Genere un secret TOTP pour l'utilisateur (ne l'active PAS encore).
    Retourne le secret, l'URI otpauth:// et le QR code en base64.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    # Generer un nouveau secret TOTP
    secret = pyotp.random_base32()

    # Stocker le secret chiffre (pas encore active)
    user.totp_secret_encrypted = encrypt_totp_secret(secret)
    db.commit()

    # Generer l'URI otpauth://
    totp = pyotp.TOTP(secret)
    otpauth_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name=TOTP_ISSUER,
    )

    # Generer le QR code en base64
    qr = qrcode.make(otpauth_uri)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "secret": secret,
        "otpauth_uri": otpauth_uri,
        "qr_code_base64": f"data:image/png;base64,{qr_base64}",
    }


def confirm_totp_setup(db: Session, user_id: int, otp_code: str) -> dict:
    """
    Verifie le premier code OTP pour confirmer le setup.
    Active le 2FA et genere les backup codes.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    if not user.totp_secret_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aucun setup 2FA en cours")

    # Dechiffrer le secret et verifier le code
    secret = decrypt_totp_secret(user.totp_secret_encrypted)
    totp = pyotp.TOTP(secret)

    if not totp.verify(otp_code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code OTP invalide")

    # Generer les backup codes
    backup_codes = generate_backup_codes(8)

    # Activer le 2FA
    user.two_factor_enabled = True
    user.backup_codes_hash = hash_backup_codes(backup_codes)
    db.commit()

    return {"backup_codes": backup_codes}


def verify_totp(db: Session, user_id: int, otp_code: str) -> bool:
    """
    Verifie un code TOTP pendant le login.
    Fenetre de tolerance : ±1 periode (30s).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.two_factor_enabled or not user.totp_secret_encrypted:
        return False

    secret = decrypt_totp_secret(user.totp_secret_encrypted)
    totp = pyotp.TOTP(secret)
    return totp.verify(otp_code, valid_window=1)


def verify_and_consume_backup_code(db: Session, user_id: int, code: str) -> bool:
    """
    Verifie et consomme un code de secours.
    Le code est retire de la liste apres utilisation.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.backup_codes_hash:
        return False

    valid, updated_json = verify_backup_code(code, user.backup_codes_hash)
    if valid and updated_json is not None:
        user.backup_codes_hash = updated_json
        db.commit()
        return True

    return False


def disable_totp(db: Session, user_id: int, otp_code: str) -> None:
    """
    Desactive le 2FA (requiert un code OTP valide).
    Supprime le secret et les backup codes.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    if not user.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA non active")

    # Verifier le code OTP
    if not verify_totp(db, user_id, otp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code OTP invalide")

    # Desactiver le 2FA
    user.two_factor_enabled = False
    user.totp_secret_encrypted = None
    user.backup_codes_hash = None
    # Revoquer tous les appareils de confiance
    db.query(TrustedDevice).filter(TrustedDevice.user_id == user_id).delete()
    db.commit()


def admin_reset_totp(db: Session, user_id: int) -> None:
    """
    Reset admin du 2FA d'un utilisateur (pas besoin de code OTP).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    user.two_factor_enabled = False
    user.totp_secret_encrypted = None
    user.backup_codes_hash = None
    # Revoquer tous les appareils de confiance
    db.query(TrustedDevice).filter(TrustedDevice.user_id == user_id).delete()
    db.commit()


def admin_reset_all_totp(db: Session, user_ids: list[int] | None = None) -> int:
    """
    Reset admin du 2FA des utilisateurs (post-restauration).
    Si user_ids est fourni, ne reset que ces utilisateurs.
    Sinon, reset tous les utilisateurs avec 2FA actif.
    Retourne le nombre d'utilisateurs affectes.
    """
    base_filter = db.query(User).filter(User.two_factor_enabled == True)
    if user_ids:
        base_filter = base_filter.filter(User.id.in_(user_ids))

    affected_count = base_filter.count()

    if affected_count > 0:
        base_filter.update({
            User.two_factor_enabled: False,
            User.totp_secret_encrypted: None,
            User.backup_codes_hash: None,
        }, synchronize_session='fetch')

    # Supprimer les appareils de confiance
    if user_ids:
        db.query(TrustedDevice).filter(TrustedDevice.user_id.in_(user_ids)).delete(synchronize_session='fetch')
    else:
        db.query(TrustedDevice).delete()

    db.commit()
    return affected_count


def get_users_with_2fa(db: Session) -> list[dict]:
    """Retourne la liste simplifiee des utilisateurs avec 2FA actif."""
    users = db.query(User).filter(User.two_factor_enabled == True).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "name": u.name or "",
            "family_name": u.family_name or "",
        }
        for u in users
    ]


def regenerate_backup_codes(db: Session, user_id: int, otp_code: str) -> dict:
    """
    Regenere les codes de secours (requiert un code OTP valide).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouve")

    if not user.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA non active")

    # Verifier le code OTP
    if not verify_totp(db, user_id, otp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code OTP invalide")

    # Generer de nouveaux codes
    backup_codes = generate_backup_codes(8)
    user.backup_codes_hash = hash_backup_codes(backup_codes)
    db.commit()

    return {"backup_codes": backup_codes}


# ========================================================================
# Appareils de confiance (Trusted Devices)
# ========================================================================

TRUSTED_DEVICE_DAYS = 30


def _hash_device_token(token: str) -> str:
    """Hash SHA-256 d'un device token."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_trusted_device(db: Session, user_id: int, user_agent: str = None) -> str:
    """
    Cree un appareil de confiance pour l'utilisateur.
    Retourne le device token en clair (a stocker cote client).
    """
    device_token = uuid.uuid4().hex
    device = TrustedDevice(
        user_id=user_id,
        device_token_hash=_hash_device_token(device_token),
        user_agent=user_agent[:500] if user_agent else None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=TRUSTED_DEVICE_DAYS),
    )
    db.add(device)
    db.commit()
    return device_token


def verify_trusted_device(db: Session, user_id: int, device_token: str) -> bool:
    """
    Verifie un device token. Retourne True si valide et non expire.
    Met a jour last_used_at en cas de succes.
    """
    token_hash = _hash_device_token(device_token)
    device = db.query(TrustedDevice).filter(
        TrustedDevice.user_id == user_id,
        TrustedDevice.device_token_hash == token_hash,
    ).first()

    if not device:
        return False

    if device.expires_at < datetime.now(timezone.utc):
        db.delete(device)
        db.commit()
        return False

    device.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return True


def revoke_trusted_devices(db: Session, user_id: int) -> int:
    """Supprime tous les appareils de confiance d'un utilisateur."""
    count = db.query(TrustedDevice).filter(TrustedDevice.user_id == user_id).delete()
    db.commit()
    return count


def revoke_trusted_device(db: Session, user_id: int, device_id: int) -> bool:
    """Supprime un appareil de confiance specifique."""
    device = db.query(TrustedDevice).filter(
        TrustedDevice.id == device_id,
        TrustedDevice.user_id == user_id,
    ).first()
    if not device:
        return False
    db.delete(device)
    db.commit()
    return True


def get_trusted_devices(db: Session, user_id: int) -> list:
    """Liste les appareils de confiance d'un utilisateur."""
    devices = db.query(TrustedDevice).filter(
        TrustedDevice.user_id == user_id,
    ).order_by(TrustedDevice.last_used_at.desc()).all()
    return [
        {
            "id": d.id,
            "user_agent": d.user_agent,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "expires_at": d.expires_at.isoformat() if d.expires_at else None,
            "last_used_at": d.last_used_at.isoformat() if d.last_used_at else None,
        }
        for d in devices
    ]


def cleanup_expired_devices(db: Session) -> int:
    """Supprime les appareils de confiance expires."""
    count = db.query(TrustedDevice).filter(
        TrustedDevice.expires_at < datetime.now(timezone.utc)
    ).delete()
    db.commit()
    return count
