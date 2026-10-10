import os
import ipaddress
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://myshoppe:myshoppe@localhost:55432/myshoppe"
    )
    origin: str = os.getenv("PUBLIC_ORIGIN", "http://localhost:3000")
    dev_login: bool = os.getenv("DEV_LOGIN_ENABLED", "false") == "true"
    payment_mode: str = os.getenv("PAYMENT_MODE", "development")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_storage_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    media_bucket: str = os.getenv("MEDIA_BUCKET", "myshoppe-media")
    razorpay_id: str = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_secret: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    webhook_secret: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    db_pool_size: str = os.getenv("DB_POOL_SIZE", "")
    db_pool_overflow: str = os.getenv("DB_POOL_OVERFLOW", "")
    media_storage_mode: str = os.getenv("MEDIA_STORAGE_MODE", "local")
    db_role: str = os.getenv("DB_ROLE", "api")
    trusted_proxy_cidrs: str = os.getenv("TRUSTED_PROXY_CIDRS", "")
    rate_limit_hmac_key: str = os.getenv("RATE_LIMIT_HMAC_KEY", "")

    def validate(self):
        if self.environment == "production":
            if self.dev_login or self.payment_mode != "razorpay":
                raise RuntimeError("Production forbids development identity and payments")
            if not all(
                [
                    self.supabase_url,
                    self.supabase_key,
                    self.razorpay_id,
                    self.razorpay_secret,
                    self.webhook_secret,
                ]
            ):
                raise RuntimeError("Production identity/payment configuration is incomplete")
            if not self.supabase_storage_key:
                raise RuntimeError("Production media storage service key is not configured")
            if not self.origin.startswith("https://"):
                raise RuntimeError("Production requires HTTPS")
            if self.media_storage_mode != "object":
                raise RuntimeError("Production requires portable object storage (MEDIA_STORAGE_MODE=object)")
            if not self.trusted_proxy_cidrs or len(self.rate_limit_hmac_key) < 32:
                raise RuntimeError("Production requires trusted proxy CIDRs and a 32-character rate-limit key")
            try:
                for cidr in self.trusted_proxy_cidrs.split(","):
                    ipaddress.ip_network(cidr.strip(), strict=False)
            except ValueError as exc:
                raise RuntimeError("TRUSTED_PROXY_CIDRS contains an invalid network") from exc


settings = Settings()
