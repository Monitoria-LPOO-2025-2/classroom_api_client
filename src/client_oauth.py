import os
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

load_dotenv()


class ClassroomClient:
    """A client for interacting with the Google Classroom API using OAuth 2.0 authentication."""

    _instance = None

    def __new__(cls, *args, **kwargs) -> "ClassroomClient":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, scopes: Optional[List[str]] = None) -> None:
        if hasattr(self, "_initialized"):
            return

        # OAuth 2.0 configuration
        self.client_id: str = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri: str = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://localhost:8080/callback"
        )

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables"
            )

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
        self.credentials = None
        self.service: Resource = self._get_service()
        self._initialized = True

    def _get_credentials(self):
        """Get OAuth 2.0 credentials, handling the flow if needed."""
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
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                }

                flow = InstalledAppFlow.from_client_config(client_config, self.scopes)
                creds = flow.run_local_server(port=8080)

            # Save credentials for next run
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)

        return creds

    def _get_service(self) -> Resource:
        """Builds and returns a Google Classroom API service object using OAuth 2.0."""
        self.credentials = self._get_credentials()
        return build("classroom", "v1", credentials=self.credentials)

    def reset_credentials(self) -> None:
        """Reset stored credentials to force re-authentication."""
        token_file = Path("token.pickle")
        if token_file.exists():
            token_file.unlink()
        print("Credentials reset. You'll be prompted to authenticate on next API call.")
