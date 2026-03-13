"""
Utilitaires cryptographiques pour le 2FA (TOTP).

Fournit le chiffrement/dechiffrement des secrets TOTP (Fernet/AES)
et la generation/verification des codes de secours (bcrypt).
"""

import secrets
import string
import json
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from app.config.config import settings

# Context bcrypt dedie aux backup codes (separe de celui des mots de passe)
_backup_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_fernet() -> Fernet:
    """Retourne une instance Fernet a partir de la cle configuree."""
    key = settings.TOTP_ENCRYPTION_KEY
    if not key:
        raise RuntimeError("TOTP_ENCRYPTION_KEY non configuree dans .env")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_totp_secret(secret: str) -> str:
    """Chiffre un secret TOTP avec Fernet (AES-128-CBC)."""
    f = _get_fernet()
    return f.encrypt(secret.encode()).decode()


def decrypt_totp_secret(encrypted: str) -> str:
    """Dechiffre un secret TOTP chiffre avec Fernet."""
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()


def generate_backup_codes(count: int = 8) -> list[str]:
    """
    Genere une liste de codes de secours alphanumeriques.
    Chaque code fait 8 caracteres (majuscules + chiffres), format XXXX-XXXX.
    """
    alphabet = string.ascii_uppercase + string.digits
    codes = []
    for _ in range(count):
        raw = ''.join(secrets.choice(alphabet) for _ in range(8))
        # Format lisible : XXXX-XXXX
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes


def hash_backup_codes(codes: list[str]) -> str:
    """
    Hash une liste de backup codes avec bcrypt et retourne un JSON array.
    Les codes sont normalises (sans tiret, en majuscules) avant le hash.
    """
    hashed = []
    for code in codes:
        normalized = code.replace("-", "").upper()
        hashed.append(_backup_pwd_context.hash(normalized))
    return json.dumps(hashed)


def verify_backup_code(code: str, hashed_codes_json: str) -> tuple[bool, str | None]:
    """
    Verifie un backup code contre la liste de codes hashes.

    Retourne (True, updated_json) si le code est valide (le code consomme est retire).
    Retourne (False, None) si le code est invalide.
    """
    normalized = code.replace("-", "").replace(" ", "").upper()
    hashed_list: list[str] = json.loads(hashed_codes_json)

    for i, hashed in enumerate(hashed_list):
        if _backup_pwd_context.verify(normalized, hashed):
            # Consommer le code (le retirer de la liste)
            hashed_list.pop(i)
            return True, json.dumps(hashed_list)

    return False, None
