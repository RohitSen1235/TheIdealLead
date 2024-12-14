from dotenv import load_dotenv
import os
from typing import List

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Email Settings
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")

    # AI Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./leads.db")

    # Server Settings
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")

    # Validation
    @property
    def is_email_configured(self) -> bool:
        return all([
            self.EMAIL_HOST,
            self.EMAIL_PORT,
            self.EMAIL_USERNAME,
            self.EMAIL_PASSWORD,
            self.EMAIL_FROM
        ])

    @property
    def is_ai_configured(self) -> bool:
        return bool(self.GROQ_API_KEY)

# Create a global settings instance
settings = Settings()
