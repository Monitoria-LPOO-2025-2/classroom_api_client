import os
from typing import Dict, Optional
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build, Resource

load_dotenv()


class ClassroomClient:
    """A client for interacting with the Google Classroom API using service account credentials from environment variables."""

    _instance = None

    def __new__(cls, *args, **kwargs) -> "ClassroomClient":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, credentials_info: Optional[Dict[str, str]] = None) -> None:
        if hasattr(self, "_initialized"):
            return

        self.scopes = [
            "https://www.googleapis.com/auth/classroom.courses",
            "https://www.googleapis.com/auth/classroom.rosters",
            "https://www.googleapis.com/auth/classroom.coursework.students",
            "https://www.googleapis.com/auth/classroom.coursework.me",
        ]

        self.course_id: str = os.getenv("COURSE_ID", "")
        self.credentials: Credentials = self._get_credentials_from_env()
        self.service: Resource = self._get_service()
        self._initialized = True

    def _get_credentials_from_env(self) -> Credentials:
        """Creates service account credentials from environment variables."""
        # Build the service account info from environment variables
        service_account_info = {
            "type": "service_account",
            "project_id": os.getenv("GOOGLE_PROJECT_ID", "your-project-id"),
            "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
            "private_key": os.getenv(
                "GOOGLE_PRIVATE_KEY"
            ),  # Don't modify the key format
            "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "auth_uri": os.getenv(
                "GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": os.getenv(
                "GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token"
            ),
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
        }

        # Remove None values
        service_account_info = {
            k: v for k, v in service_account_info.items() if v is not None
        }

        # Validate required fields
        required_fields = ["private_key", "client_email"]
        missing_fields = [
            field for field in required_fields if not service_account_info.get(field)
        ]

        if missing_fields:
            raise ValueError(
                f"Missing required environment variables for service account: {missing_fields}"
            )

        return Credentials.from_service_account_info(
            service_account_info, scopes=self.scopes
        )

    def _get_service(self) -> Resource:
        """Builds and returns a Google Classroom API service object."""
        return build("classroom", "v1", credentials=self.credentials)
