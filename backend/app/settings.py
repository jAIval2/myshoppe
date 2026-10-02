import os
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
    razorpay_id: str = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_secret: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    webhook_secret: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

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
            if not self.origin.startswith("https://"):
                raise RuntimeError("Production requires HTTPS")


settings = Settings()
