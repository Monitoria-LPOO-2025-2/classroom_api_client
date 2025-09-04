import os
import pickle
import socket
from typing import List, Optional
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
                    "https://www.googleapis.com/auth/drive.readonly",
                ]

        self.scopes: List[str] = scopes
        self.course_id: str = os.getenv("COURSE_ID", "")
        self.credentials = None
        self.service: Resource = self._get_service()
        self._initialized = True

    def _find_free_port(self, start_port: int = 8080, max_attempts: int = 10) -> int:
        """Find a free port starting from start_port."""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                    return port
            except OSError:
                continue
        raise RuntimeError(
            f"Could not find free port in range {start_port}-{start_port + max_attempts}"
        )

    def _get_credentials(self):
        """Get OAuth 2.0 credentials, handling the flow if needed."""
        creds = None
        token_file = Path("token.pickle")
        credentials_file = Path("credentials.json")

        # Load existing credentials from file
        if token_file.exists():
            with open(token_file, "rb") as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Use credentials.json file if it exists
                if credentials_file.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_file), self.scopes
                    )
                    # Find a free port
                    free_port = self._find_free_port()
                    print(f"Starting OAuth server on port {free_port}...")
                    creds = flow.run_local_server(port=free_port)
                else:
                    # Fallback to environment variables
                    client_id = os.getenv("GOOGLE_CLIENT_ID")
                    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
                    redirect_uri = os.getenv(
                        "GOOGLE_REDIRECT_URI", "http://localhost:8080/callback"
                    )

                    if (
                        not client_id
                        or not client_secret
                        or client_id == "your_client_id_here"
                    ):
                        raise ValueError(
                            "Either place credentials.json file in the project root, "
                            "or set valid GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment variables"
                        )

                    # Create credentials dict for OAuth flow
                    client_config = {
                        "installed": {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": [redirect_uri],
                        }
                    }

                    flow = InstalledAppFlow.from_client_config(
                        client_config, self.scopes
                    )
                    # Find a free port
                    free_port = self._find_free_port()
                    print(f"Starting OAuth server on port {free_port}...")
                    creds = flow.run_local_server(port=free_port)

            # Save credentials for next run
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)

        return creds

    def _get_service(self) -> Resource:
        """Builds and returns a Google Classroom API service object using OAuth 2.0."""
        self.credentials = self._get_credentials()
        return build("classroom", "v1", credentials=self.credentials)

    def get_drive_service(self) -> Resource:
        """Builds and returns a Google Drive API service object."""
        if not hasattr(self, "credentials") or self.credentials is None:
            self.credentials = self._get_credentials()
        return build("drive", "v3", credentials=self.credentials)

    def reset_credentials(self) -> None:
        """Reset stored credentials to force re-authentication."""
        token_file = Path("token.pickle")
        if token_file.exists():
            token_file.unlink()
        print("Credentials reset. You'll be prompted to authenticate on next API call.")
