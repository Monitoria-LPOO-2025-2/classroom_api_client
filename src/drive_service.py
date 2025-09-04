from typing import Dict, Any, List
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
        download_path.mkdir(parents=True, exist_ok=True)

        try:
            file_metadata = self.drive_service.files().get(fileId=file_id).execute()
            actual_file_name = file_metadata.get("name", file_name)

            if actual_file_name:
                file_name = actual_file_name

            print(f"📄 Processing file: {file_name} (ID: {file_id})")
        except Exception as e:
            print(f"⚠️  Warning: Could not get file metadata for {file_id}: {e}")
            # Continue with provided filename
            file_metadata = {"mimeType": "application/octet-stream"}

        # Sanitize filename for filesystem
        safe_file_name = self._sanitize_filename(file_name)
        file_path = download_path / safe_file_name

        try:
            # Check if it's a Google Workspace file that needs exporting
            mime_type = file_metadata.get("mimeType", "")
            if mime_type.startswith("application/vnd.google-apps."):
                return self._export_google_file(
                    file_id, safe_file_name, download_path, file_metadata
                )

            # For regular files, download directly
            request = self.drive_service.files().get_media(fileId=file_id)

            # Download file
            with open(file_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        print(f"   📥 Download progress: {progress}%", end="\r")

            print(f"\n✅ Downloaded: {file_path}")
            return str(file_path)

        except Exception as e:
            # Handle Google Docs/Sheets/Slides files that need to be exported
            if "does not support downloading" in str(e) or "Use Export" in str(e):
                return self._export_google_file(
                    file_id, safe_file_name, download_path, file_metadata
                )
            else:
                print(f"❌ Error downloading file {file_name}: {e}")
                raise

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')

        # Ensure filename is not empty
        if not filename:
            filename = "unnamed_file"

        return filename

    def _export_google_file(
        self,
        file_id: str,
        file_name: str,
        download_path: Path,
        file_metadata: Dict[str, Any],
    ) -> str:
        """Export Google Docs/Sheets/Slides files to downloadable formats."""
        mime_type = file_metadata.get("mimeType", "")

        print(f"📋 Exporting Google Workspace file: {file_name}")

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
            "application/vnd.google-apps.form": ("application/pdf", ".pdf"),
            "application/vnd.google-apps.script": ("application/json", ".json"),
        }

        if mime_type in export_formats:
            export_mime_type, extension = export_formats[mime_type]

            # Add appropriate extension if not present
            if not file_name.lower().endswith(extension.lower()):
                # Remove any existing extension first
                name_without_ext = Path(file_name).stem
                file_name = f"{name_without_ext}{extension}"

            file_path = download_path / file_name

            try:
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
                            progress = int(status.progress() * 100)
                            print(f"   📤 Export progress: {progress}%", end="\r")

                print(f"\n✅ Exported: {file_path}")
                return str(file_path)

            except Exception as e:
                print(f"❌ Error exporting {file_name}: {e}")
                # Try to export as PDF as fallback
                try:
                    pdf_file_name = f"{Path(file_name).stem}.pdf"
                    pdf_file_path = download_path / pdf_file_name

                    request = self.drive_service.files().export_media(
                        fileId=file_id, mimeType="application/pdf"
                    )

                    with open(pdf_file_path, "wb") as f:
                        downloader = MediaIoBaseDownload(f, request)
                        done = False
                        while done is False:
                            status, done = downloader.next_chunk()

                    print(f"✅ Exported as PDF fallback: {pdf_file_path}")
                    return str(pdf_file_path)

                except Exception as fallback_error:
                    print(f"❌ PDF fallback also failed: {fallback_error}")
                    raise e
        else:
            print(f"❌ Unsupported file type for export: {mime_type}")
            raise ValueError(f"Cannot download or export file type: {mime_type}")

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get information about a file from Google Drive."""
        try:
            return (
                self.drive_service.files()
                .get(fileId=file_id, fields="id,name,mimeType,size,webViewLink,createdTime,modifiedTime")
                .execute()
            )
        except Exception as e:
            print(f"❌ Error getting file info for {file_id}: {e}")
            raise

    def download_submission_attachments(
        self,
        attachments: List[Dict[str, Any]],
        download_folder: str = "downloads",
        student_name: str = None,
    ) -> List[str]:
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

        # Create student folder structure
        if student_name:
            # Sanitize student name for use as folder name
            safe_student_name = self._sanitize_filename(student_name)
            safe_student_name = safe_student_name.replace(" ", "_")
            student_folder = f"{download_folder}/{safe_student_name}"
        else:
            student_folder = download_folder

        # Always create the student directory, even if there are no files
        student_path = Path(student_folder)
        student_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created/verified directory: {student_folder}")

        # Check if there are any attachments
        if not attachments:
            print(f"📝 No attachments found for {student_name or 'student'}")
            # Create an empty marker file to indicate the student submitted but with no attachments
            marker_file = student_path / "_no_attachments.txt"
            with open(marker_file, "w", encoding="utf-8") as f:
                f.write(f"Student: {student_name or 'Unknown'}\n")
                f.write("Status: Submitted with no file attachments\n")
                f.write("Directory created on download\n")
            print(f"📄 Created marker file: {marker_file}")
            return downloaded_files

        print(f"🔍 Processing {len(attachments)} attachment(s) for {student_name or 'student'}")

        # Process each attachment
        for i, attachment in enumerate(attachments, 1):
            print(f"\n📎 [{i}/{len(attachments)}] Processing attachment...")

            try:
                # Handle different attachment types
                if "driveFile" in attachment:
                    drive_file = attachment["driveFile"]
                    file_id = drive_file.get("id")
                    file_title = drive_file.get("title", f"file_{file_id}")

                    if not file_id:
                        print("⚠️  Skipping attachment: No file ID found")
                        continue

                    print(f"   📄 Drive file: {file_title}")

                    file_path = self.download_file(file_id, file_title, student_folder)
                    downloaded_files.append(file_path)

                elif "youTubeVideo" in attachment:
                    youtube_video = attachment["youTubeVideo"]
                    video_id = youtube_video.get("id", "")
                    video_title = youtube_video.get("title", f"YouTube_Video_{video_id}")

                    print(f"   🎥 YouTube video: {video_title}")

                    # Create a text file with YouTube link info
                    youtube_file = student_path / f"{self._sanitize_filename(video_title)}.txt"
                    with open(youtube_file, "w", encoding="utf-8") as f:
                        f.write("YouTube Video Submission\n")
                        f.write(f"Title: {video_title}\n")
                        f.write(f"Video ID: {video_id}\n")
                        f.write(f"URL: https://www.youtube.com/watch?v={video_id}\n")

                    downloaded_files.append(str(youtube_file))
                    print(f"   ✅ Created YouTube info file: {youtube_file}")

                elif "link" in attachment:
                    link = attachment["link"]
                    url = link.get("url", "")
                    title = link.get("title", "Link")

                    print(f"   🔗 Link: {title}")

                    # Create a text file with link info
                    link_file = student_path / f"{self._sanitize_filename(title)}_link.txt"
                    with open(link_file, "w", encoding="utf-8") as f:
                        f.write("Link Submission\n")
                        f.write(f"Title: {title}\n")
                        f.write(f"URL: {url}\n")

                    downloaded_files.append(str(link_file))
                    print(f"   ✅ Created link info file: {link_file}")

                else:
                    print(f"   ⚠️  Unknown attachment type: {list(attachment.keys())}")

                    # Create a debug file with the attachment info
                    debug_file = student_path / f"unknown_attachment_{i}.json"
                    import json
                    with open(debug_file, "w", encoding="utf-8") as f:
                        json.dump(attachment, f, indent=2)

                    downloaded_files.append(str(debug_file))
                    print(f"   📄 Created debug file: {debug_file}")

            except Exception as e:
                print(f"   ❌ Error processing attachment {i}: {e}")

                # Create an error log file
                error_file = student_path / f"error_attachment_{i}.txt"
                with open(error_file, "w", encoding="utf-8") as f:
                    f.write(f"Error processing attachment {i}\n")
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"Attachment data: {attachment}\n")

                print(f"   📄 Created error log: {error_file}")

        if downloaded_files:
            print(f"\n✅ Successfully processed {len(downloaded_files)} item(s) for {student_name or 'student'}")
        else:
            print(f"\n⚠️  No files were successfully downloaded for {student_name or 'student'}")

        return downloaded_files
