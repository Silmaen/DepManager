from pathlib import Path

from cryptography.fernet import Fernet
from api.internal.messaging import log


class PasswordManager:
    """Manage password encryption and decryption."""

    ENCRYPTED_PREFIX = "encrypted:"

    def __init__(self, base_path: Path):
        self.key_file = base_path / ".key"
        self._ensure_key()
        self.cipher = Fernet(self._load_key())

    def _ensure_key(self):
        """Create an encryption key if it does not exist."""
        if not self.key_file.exists():
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            self.key_file.chmod(0o600)  # Lecture/écriture propriétaire uniquement

    def _load_key(self) -> bytes:
        """Load the encryption key from the key file."""
        return self.key_file.read_bytes()

    def encrypt(self, password: str) -> str:
        """Crypt a password."""
        if not password:
            return ""
        encrypted = self.cipher.encrypt(password.encode()).decode()
        return f"{self.ENCRYPTED_PREFIX}{encrypted}"

    def decrypt(self, encrypted: str) -> str:
        """Decrypt a password."""
        if not encrypted:
            return ""
        if encrypted.startswith(self.ENCRYPTED_PREFIX):
            encrypted_part = encrypted[len(self.ENCRYPTED_PREFIX) :]
            try:
                return self.cipher.decrypt(encrypted_part.encode()).decode()
            except Exception as e:
                log.error(f"Failed to decrypt password: {e}")
                # if decryption fails, return the encrypted string
                return encrypted
        log.warn(f"Your password is not stored encrypted.")
        # If not encrypted, return as is
        return encrypted
