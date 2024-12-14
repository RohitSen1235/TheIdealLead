from dotenv import load_dotenv
import os
from typing import List, Dict
import json

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

    # Proxy Settings
    # Now supports both single proxy and multiple proxies
    PROXY_URLS: List[Dict[str, str]] = []
    
    def __init__(self):
        # Initialize proxy settings
        self._initialize_proxy_settings()
    
    def _initialize_proxy_settings(self):
        # First try to load multiple proxies from PROXY_LIST
        proxy_list = os.getenv("PROXY_LIST", "")
        if proxy_list:
            try:
                # Expect JSON array of proxy objects
                self.PROXY_URLS = json.loads(proxy_list)
            except json.JSONDecodeError:
                print("Warning: Invalid PROXY_LIST format. Falling back to single proxy.")
        
        # If no proxy list, try single proxy configuration
        if not self.PROXY_URLS and os.getenv("PROXY_URL"):
            proxy = {
                "url": os.getenv("PROXY_URL", ""),
                "username": os.getenv("PROXY_USERNAME", ""),
                "password": os.getenv("PROXY_PASSWORD", "")
            }
            if proxy["url"]:
                self.PROXY_URLS.append(proxy)

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

    @property
    def is_proxy_configured(self) -> bool:
        return len(self.PROXY_URLS) > 0

# Create a global settings instance
settings = Settings()
