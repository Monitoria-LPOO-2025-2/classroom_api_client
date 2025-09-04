import os
import pickle
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

load_dotenv()


class ClassroomClient:
    """A client for interacting with the Google Classroom API supporting both OAuth 2.0 and Service Account authentication."""

    _instance = None

    def __new__(cls, *args, **kwargs) -> "ClassroomClient":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self, scopes: Optional[List[str]] = None, use_service_account: bool = True
    ) -> None:
        if hasattr(self, "_initialized"):
            return

        # Scopes for Google Classroom API
        if scopes is None:
            scopes_env = os.getenv("GOOGLE_SCOPES", "")
            if scopes_env:
                scopes = scopes_env.split(",")
            else:
                scopes = [
                    "https://www.googleapis.com/auth/classroom.courses",
                    "https://www.googleapis.com/auth/classroom.rosters",
                    "https://www.googleapis.com/auth/classroom.coursework.students",
                    "https://www.googleapis.com/auth/classroom.coursework.me",
                ]

        self.scopes: List[str] = scopes
        self.course_id: str = os.getenv("COURSE_ID", "")
        self.use_service_account = use_service_account
        self.credentials = None
        self.service: Resource = self._get_service()
        self._initialized = True

    def _get_service_account_credentials(self) -> ServiceAccountCredentials:
        """Get service account credentials from JSON file."""
        json_file = Path("credentials.json")
        if json_file.exists():
            return ServiceAccountCredentials.from_service_account_file(
                str(json_file), scopes=self.scopes
            )
        else:
            raise FileNotFoundError(
                "Service account JSON file 'credentials.json' not found"
            )

    def _get_oauth_credentials(self):
        """Get OAuth 2.0 credentials, handling the flow if needed."""
        # OAuth 2.0 configuration
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://localhost:8080/callback"
        )

        if not client_id or not client_secret or client_id == "your_client_id_here":
            raise ValueError(
                "Valid GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables"
            )

        creds = None
        token_file = Path("token.pickle")

        # Load existing credentials from file
        if token_file.exists():
            with open(token_file, "rb") as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Create credentials dict for OAuth flow
                client_config = {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri],
                    }
                }

                flow = InstalledAppFlow.from_client_config(client_config, self.scopes)
                creds = flow.run_local_server(port=8080)

            # Save credentials for next run
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)

        return creds

    def _get_credentials(self):
        """Get credentials using the preferred method."""
        if self.use_service_account:
            try:
                return self._get_service_account_credentials()
            except FileNotFoundError:
                print("Service account file not found, falling back to OAuth 2.0...")
                return self._get_oauth_credentials()
        else:
            return self._get_oauth_credentials()

    def _get_service(self) -> Resource:
        """Builds and returns a Google Classroom API service object."""
        self.credentials = self._get_credentials()
        return build("classroom", "v1", credentials=self.credentials)

    def reset_oauth_credentials(self) -> None:
        """Reset stored OAuth credentials to force re-authentication."""
        token_file = Path("token.pickle")
        if token_file.exists():
            token_file.unlink()
        print(
            "OAuth credentials reset. You'll be prompted to authenticate on next API call."
        )

    def switch_to_oauth(self) -> None:
        """Switch to OAuth 2.0 authentication."""
        self.use_service_account = False
        self.credentials = None
        self.service = self._get_service()
        print("Switched to OAuth 2.0 authentication.")

    def switch_to_service_account(self) -> None:
        """Switch to service account authentication."""
        self.use_service_account = True
        self.credentials = None
        self.service = self._get_service()
        print("Switched to service account authentication.")
