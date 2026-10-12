"""Puertos e implementación de hashing de contraseñas."""

from typing import Protocol

from pwdlib import PasswordHash


class PasswordHasher(Protocol):
    """Puerto reemplazable para hashing y verificación de passwords."""

    def hash(self, plain_password: str) -> str:
        """Genera un hash seguro para una contraseña en claro."""

    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Verifica una contraseña en claro contra un hash persistido."""


class PwdlibPasswordHasher:
    """PasswordHasher basado en Argon2id mediante pwdlib."""

    def __init__(self, password_hash: PasswordHash | None = None) -> None:
        self._password_hash = password_hash or PasswordHash.recommended()

    def hash(self, plain_password: str) -> str:
        return self._password_hash.hash(plain_password)

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return self._password_hash.verify(plain_password, password_hash)
