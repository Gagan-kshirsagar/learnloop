from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt

from app.modules.identity.internal.schemas import TokenPayload
from app.shared.config import get_settings


class AuthProvider(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a plaintext password."""

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hash."""

    @abstractmethod
    def create_access_token(self, user_id: UUID, tenant_id: UUID, role: str) -> str:
        """Create a signed access token."""

    @abstractmethod
    def create_refresh_token(self, user_id: UUID, tenant_id: UUID, role: str) -> str:
        """Create a signed refresh token."""

    @abstractmethod
    def verify_token(self, token: str, expected_type: str | None = None) -> TokenPayload:
        """Verify and decode a signed token."""


class JwtAuthProvider(AuthProvider):
    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str | None = None,
        access_expire_minutes: int | None = None,
        refresh_expire_days: int | None = None,
    ) -> None:
        settings = get_settings()
        self.secret_key = secret_key or settings.jwt_secret_key
        self.algorithm = algorithm or settings.jwt_algorithm
        self.access_expire_minutes = access_expire_minutes or settings.access_token_expire_minutes
        self.refresh_expire_days = refresh_expire_days or settings.refresh_token_expire_days

    def hash_password(self, password: str) -> str:
        pwd_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            pwd_bytes = plain_password.encode("utf-8")[:72]
            hash_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(pwd_bytes, hash_bytes)
        except Exception:
            return False

    def create_access_token(self, user_id: UUID, tenant_id: UUID, role: str) -> str:
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=self.access_expire_minutes)
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "role": role,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: UUID, tenant_id: UUID, role: str) -> str:
        now = datetime.now(UTC)
        exp = now + timedelta(days=self.refresh_expire_days)
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "role": role,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, expected_type: str | None = None) -> TokenPayload:
        try:
            payload_dict = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            token_payload = TokenPayload(**payload_dict)
        except (jwt.PyJWTError, Exception) as exc:
            raise ValueError(f"Invalid or expired token: {exc}") from exc

        if expected_type and token_payload.type != expected_type:
            msg = f"Invalid token type: expected '{expected_type}', got '{token_payload.type}'"
            raise ValueError(msg)

        return token_payload


class FirebaseAuthProvider(AuthProvider):
    def hash_password(self, password: str) -> str:
        raise NotImplementedError("Firebase auth provider is not configured")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        raise NotImplementedError("Firebase auth provider is not configured")

    def create_access_token(self, user_id: UUID, tenant_id: UUID, role: str) -> str:
        raise NotImplementedError("Firebase auth provider is not configured")

    def create_refresh_token(self, user_id: UUID, tenant_id: UUID, role: str) -> str:
        raise NotImplementedError("Firebase auth provider is not configured")

    def verify_token(self, token: str, expected_type: str | None = None) -> TokenPayload:
        raise NotImplementedError("Firebase auth provider is not configured")


def get_auth_provider(provider_type: str | None = None) -> AuthProvider:
    selected = (provider_type or get_settings().auth_provider).lower()
    if selected == "jwt":
        return JwtAuthProvider()
    if selected == "firebase":
        return FirebaseAuthProvider()
    raise ValueError(f"Unsupported auth provider: '{selected}'")
