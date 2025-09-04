from typing import Dict, Any
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from client import ClassroomClient


class DriveService:
    """A service for downloading files from Google Drive."""

    def __init__(self, client: ClassroomClient) -> None:
        self.client: ClassroomClient = client
        self.drive_service = client.get_drive_service()

    def download_file(
        self, file_id: str, file_name: str, download_folder: str = "downloads"
    ) -> str:
        """
        Download a file from Google Drive.

        Args:
            file_id: The Google Drive file ID
            file_name: The name to save the file as
            download_folder: The folder to save the file in

        Returns:
            The path to the downloaded file
        """
        # Create download folder if it doesn't exist
        download_path = Path(download_folder)
        download_path.mkdir(exist_ok=True)

        # Get file metadata
        file_metadata = self.drive_service.files().get(fileId=file_id).execute()
        file_name = file_name or file_metadata.get("name", f"file_{file_id}")

        # Full path for the downloaded file
        file_path = download_path / file_name

        try:
            # Request file content
            request = self.drive_service.files().get_media(fileId=file_id)

            # Download file
            with open(file_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        print(f"Download progress: {int(status.progress() * 100)}%")

            print(f"✅ Downloaded: {file_path}")
            return str(file_path)

        except Exception as e:
            # Handle Google Docs/Sheets/Slides files that need to be exported
            if "does not support downloading" in str(e) or "Use Export" in str(e):
                return self._export_google_file(
                    file_id, file_name, download_path, file_metadata
                )
            else:
                print(f"❌ Error downloading file {file_id}: {e}")
                raise

    def _export_google_file(
        self,
        file_id: str,
        file_name: str,
        download_path: Path,
        file_metadata: Dict[str, Any],
    ) -> str:
        """Export Google Docs/Sheets/Slides files to downloadable formats."""
        mime_type = file_metadata.get("mimeType", "")

        # Define export formats for different Google file types
        export_formats = {
            "application/vnd.google-apps.document": (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".docx",
            ),
            "application/vnd.google-apps.spreadsheet": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".xlsx",
            ),
            "application/vnd.google-apps.presentation": (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                ".pptx",
            ),
            "application/vnd.google-apps.drawing": ("image/png", ".png"),
        }

        if mime_type in export_formats:
            export_mime_type, extension = export_formats[mime_type]

            # Add appropriate extension if not present
            if not file_name.endswith(extension):
                file_name = f"{file_name}{extension}"

            file_path = download_path / file_name

            # Export the file
            request = self.drive_service.files().export_media(
                fileId=file_id, mimeType=export_mime_type
            )

            with open(file_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        print(f"Export progress: {int(status.progress() * 100)}%")

            print(f"✅ Exported: {file_path}")
            return str(file_path)
        else:
            print(f"❌ Unsupported file type for export: {mime_type}")
            raise ValueError(f"Cannot download or export file type: {mime_type}")

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get information about a file from Google Drive."""
        try:
            return (
                self.drive_service.files()
                .get(fileId=file_id, fields="id,name,mimeType,size,webViewLink")
                .execute()
            )
        except Exception as e:
            print(f"❌ Error getting file info for {file_id}: {e}")
            raise

    def download_submission_attachments(
        self,
        attachments: list,
        download_folder: str = "downloads",
        student_name: str = None,
    ) -> list:
        """
        Download all attachments from a submission.

        Args:
            attachments: List of attachment objects from the Classroom API
            download_folder: Folder to save files in
            student_name: Name of the student (used for folder organization)

        Returns:
            List of downloaded file paths
        """
        downloaded_files = []

        # Create a subfolder for the student if name is provided
        if student_name:
            # Sanitize student name for use as folder name
            safe_student_name = "".join(
                c for c in student_name if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            safe_student_name = safe_student_name.replace(" ", "_")
            student_folder = f"{download_folder}/{safe_student_name}"
        else:
            student_folder = download_folder

        for attachment in attachments:
            if "driveFile" in attachment:
                drive_file = attachment["driveFile"]
                file_id = drive_file["id"]
                file_name = drive_file["title"]

                try:
                    file_path = self.download_file(file_id, file_name, student_folder)
                    downloaded_files.append(file_path)
                except Exception as e:
                    print(f"❌ Failed to download {file_name}: {e}")

        return downloaded_files
