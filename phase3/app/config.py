"""
Configuration — loaded from environment variables.
Copy .env.example to .env and fill in your keys.
"""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./roadmap.db")

    def validate(self):
        if not self.GEMINI_API_KEY:
            raise EnvironmentError("GEMINI_API_KEY is not set. Check your .env file.")


settings = Settings()
