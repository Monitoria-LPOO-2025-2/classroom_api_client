import typer
import typer
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ensure local imports work when running the script directly
sys.path.insert(0, str(Path(__file__).parent))

from services import ClassroomService
from client import ClassroomClient

load_dotenv()

app = typer.Typer()

# sub-apps
auth_app = typer.Typer()
submission_app = typer.Typer()
drive_app = typer.Typer()
course_app = typer.Typer()

# mount sub-apps
app.add_typer(auth_app, name="auth")
app.add_typer(submission_app, name="submission")
app.add_typer(drive_app, name="drive")
app.add_typer(course_app, name="course")


# ----- Auth commands -----
@auth_app.command("login")
def auth_login() -> None:
    """Trigger OAuth 2.0 authentication flow."""
    try:
        client = ClassroomClient()
        client.reset_credentials()
        client = ClassroomClient()
        print("Authentication successful! You can now use the API.")
    except Exception as e:
        print(f"Authentication failed: {e}")


@auth_app.command("reset")
def auth_reset() -> None:
    """Reset stored authentication credentials."""
    client = ClassroomClient()
    client.reset_credentials()
    print("Authentication credentials have been reset.")


# ----- Course commands -----
@course_app.command("list")
def list_courses() -> None:
    """List all courses."""
    client = ClassroomClient()
    service = ClassroomService(client)
    courses = service.get_courses()
    if not courses:
        print("No courses found or insufficient permissions.")
        return
    for course in courses:
        print(f"{course['id']}: {course['name']}")


@course_app.command("get")
def get_course(course_id: str = None) -> None:
    """Get the details of a specific course. Uses COURSE_ID from .env if not provided."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        course = service.get_course(course_id)
        print(f"Course: {course}")
    except Exception as e:
        print(f"Error fetching course: {e}")


@course_app.command("current")
def get_current_course_info() -> None:
    """Get information about the course specified in COURSE_ID environment variable."""
    course_id = os.getenv("COURSE_ID")
    if not course_id:
        print("COURSE_ID not found in environment variables.")
        return

    print(f"Current course ID: {course_id}")
    get_course(course_id)


# ----- Submission commands (dependent on coursework) -----
@submission_app.command("download")
def download_submission_files(
    coursework_id: str,
    submission_id: str,
    course_id: str = None,
    download_folder: str = "downloads",
) -> None:
    """Download all files from a submission with student information."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        print(f"📥 Downloading files from submission {submission_id}...")
        result = service.download_submission_files_with_student_info(
            course_id, coursework_id, submission_id, download_folder
        )

        print(f"👤 Student: {result['student_name']}")
        print(f"📧 Email: {result['student_email']}")
        print(f"🆔 User ID: {result['user_id']}")

        if result["downloaded_files"]:
            print(
                f"✅ Successfully downloaded {len(result['downloaded_files'])} file(s):"
            )
            for file_path in result["downloaded_files"]:
                print(f"   📄 {file_path}")
        else:
            print("ℹ️  No files found to download.")

    except Exception as e:
        print(f"❌ Error downloading files: {e}")


@submission_app.command("info")
def get_submission_info(
    coursework_id: str, submission_id: str, course_id: str = None
) -> None:
    """Get detailed information about a submission including student details."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        submission_info = service.get_submission_with_student_info(
            course_id, coursework_id, submission_id
        )

        print(f"📋 Submission Information:")
        print(f"   ID: {submission_info.get('id', 'N/A')}")
        print(f"   State: {submission_info.get('state', 'N/A')}")
        print(f"   Created: {submission_info.get('creationTime', 'N/A')}")
        print(f"   Updated: {submission_info.get('updateTime', 'N/A')}")

        student_profile = submission_info.get("studentProfile", {})
        print(f"\n👤 Student Information:")
        print(f"   Name: {student_profile.get('name', {}).get('fullName', 'N/A')}")
        print(f"   Email: {student_profile.get('emailAddress', 'N/A')}")
        print(f"   User ID: {submission_info.get('userId', 'N/A')}")

        attachments = submission_info.get("assignmentSubmission", {}).get(
            "attachments", []
        )
        if attachments:
            print(f"\n📎 Attachments ({len(attachments)}):")
            for i, attachment in enumerate(attachments, 1):
                if "driveFile" in attachment:
                    drive_file = attachment["driveFile"]
                    print(
                        f"   {i}. {drive_file.get('title', 'Untitled')} (ID: {drive_file.get('id', 'N/A')})"
                    )
        else:
            print(f"\n📎 No attachments found")

    except Exception as e:
        print(f"❌ Error getting submission info: {e}")


@submission_app.command("list")
def list_submissions_with_students(coursework_id: str, course_id: str = None) -> None:
    """List all submissions with student names for an assignment."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        submissions = service.get_student_submissions(course_id, coursework_id)

        if not submissions:
            print("No submissions found for this assignment.")
            return

        print(f"📝 Submissions for assignment {coursework_id}:")
        print("-" * 80)

        for submission in submissions:
            try:
                student_profile = service.student_repository.get_student_profile(
                    submission.get("userId", "")
                )
                student_name = student_profile.get("name", {}).get(
                    "fullName", "Unknown"
                )
                student_email = student_profile.get(
                    "emailAddress", "unknown@example.com"
                )

                submission_state = submission.get("state", "UNKNOWN")
                submission_id = submission.get("id", "N/A")

                attachments = submission.get("assignmentSubmission", {}).get(
                    "attachments", []
                )
                attachment_count = len(attachments)

                print(f"👤 {student_name} ({student_email})")
                print(f"   📋 ID: {submission_id}")
                print(f"   📊 State: {submission_state}")
                print(f"   📎 Attachments: {attachment_count}")
                print()

            except Exception as e:
                print(
                    f"   ❌ Error getting info for submission {submission.get('id', 'unknown')}: {e}"
                )
                print()

    except Exception as e:
        print(f"❌ Error listing submissions: {e}")


@submission_app.command("download-all")
def download_all_submissions(
    coursework_id: str, course_id: str = None, download_folder: str = "downloads"
) -> None:
    """Download all files from all submissions in an assignment, organized by student."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        print(f"📥 Downloading all submissions for assignment {coursework_id}...")
        submissions = service.get_student_submissions(course_id, coursework_id)

        if not submissions:
            print("No submissions found for this assignment.")
            return

        total_files = 0
        successful_downloads = 0

        for i, submission in enumerate(submissions, 1):
            submission_id = submission.get("id")
            if not submission_id:
                continue

            try:
                print(
                    f"\n[{i}/{len(submissions)}] Processing submission {submission_id}..."
                )
                result = service.download_submission_files_with_student_info(
                    course_id, coursework_id, submission_id, download_folder
                )

                print(f"   👤 Student: {result['student_name']}")
                print(f"   📧 Email: {result['student_email']}")

                if result["downloaded_files"]:
                    print(
                        f"   ✅ Downloaded {len(result['downloaded_files'])} file(s):"
                    )
                    for file_path in result["downloaded_files"]:
                        print(f"      📄 {file_path}")
                    total_files += len(result["downloaded_files"])
                    successful_downloads += 1
                else:
                    print(f"   ℹ️  No files to download")

            except Exception as e:
                print(f"   ❌ Error processing submission {submission_id}: {e}")

        print(f"\n🎉 Download complete!")
        print(f"   📊 Processed {len(submissions)} submissions")
        print(f"   ✅ Successfully downloaded from {successful_downloads} submissions")
        print(f"   📄 Total files downloaded: {total_files}")

    except Exception as e:
        print(f"❌ Error downloading all submissions: {e}")


# ----- Drive commands -----
@drive_app.command("download")
def download_drive_file(
    file_id: str, file_name: str = None, download_folder: str = "downloads"
) -> None:
    """Download a specific file from Google Drive by file ID."""
    client = ClassroomClient()
    service = ClassroomService(client)

    try:
        print(f"📥 Downloading file {file_id}...")
        if not file_name:
            file_info = service.drive_service.get_file_info(file_id)
            file_name = file_info.get("name", f"file_{file_id}")

        file_path = service.drive_service.download_file(
            file_id, file_name, download_folder
        )
        print(f"✅ File downloaded successfully: {file_path}")

    except Exception as e:
        print(f"❌ Error downloading file: {e}")


@drive_app.command("info")
def get_file_info(file_id: str) -> None:
    """Get information about a Google Drive file."""
    client = ClassroomClient()
    service = ClassroomService(client)

    try:
        file_info = service.drive_service.get_file_info(file_id)
        print(f"📄 File Information:")
        print(f"   Name: {file_info.get('name', 'N/A')}")
        print(f"   ID: {file_info.get('id', 'N/A')}")
        print(f"   Type: {file_info.get('mimeType', 'N/A')}")
        print(
            f"   Size: {file_info.get('size', 'N/A')} bytes"
            if file_info.get("size")
            else "   Size: N/A (Google Docs file)"
        )
        print(f"   Link: {file_info.get('webViewLink', 'N/A')}")

    except Exception as e:
        print(f"❌ Error getting file info: {e}")


# ----- Coursework listing -----
@course_app.command("list-work")
def list_coursework(course_id: str = None) -> None:
    """List all coursework for a specific course. Uses COURSE_ID from .env if not provided."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        coursework = service.get_course_work(course_id)
        if not coursework:
            print("No coursework found for this course.")
            return
        for work in coursework:
            print(f"{work['id']}: {work['title']}")
    except Exception as e:
        print(f"Error fetching coursework: {e}")


@course_app.command("list-submissions")
def list_submissions(coursework_id: str, course_id: str = None) -> None:
    """List all submissions for a specific assignment. Uses COURSE_ID from .env if not provided."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        submissions = service.get_student_submissions(course_id, coursework_id)
        if not submissions:
            print("No submissions found for this assignment.")
            return
        for submission in submissions:
            print(f"{submission['id']}: {submission['userId']}")
    except Exception as e:
        print(f"Error fetching submissions: {e}")


@submission_app.command("list-attachments")
def list_attachments(
    coursework_id: str, submission_id: str, course_id: str = None
) -> None:
    """List all attachments for a specific submission. Uses COURSE_ID from .env if not provided."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        attachments = service.get_submission_attachments(
            course_id, coursework_id, submission_id
        )
        if not attachments:
            print("No attachments found for this submission.")
            return
        for attachment in attachments:
            print(attachment)
    except Exception as e:
        print(f"Error fetching attachments: {e}")


@submission_app.command("comment")
def add_comment(
    coursework_id: str, submission_id: str, comment: str, course_id: str = None
) -> None:
    """Add a private comment to a submission. Uses COURSE_ID from .env if not provided.

    Note: This operation may require OAuth2 authentication instead of API key.
    """
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        service.add_comment(course_id, coursework_id, submission_id, comment)
        print("Comment added successfully.")
    except Exception as e:
        print(f"Error adding comment: {e}")
        print(
            "Note: Adding comments may require OAuth2 authentication instead of API key."
        )


@submission_app.command("grade")
def patch_grade(
    coursework_id: str, submission_id: str, grade: float, course_id: str = None
) -> None:
    """Assign a grade to a submission. Uses COURSE_ID from .env if not provided.

    Note: This operation may require OAuth2 authentication instead of API key.
    """
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print(
                "No course ID provided and COURSE_ID not found in environment variables."
            )
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        service.patch_grade(course_id, coursework_id, submission_id, grade)
        print("Grade assigned successfully.")
    except Exception as e:
        print(f"Error assigning grade: {e}")
        print("Note: Grading may require OAuth2 authentication instead of API key.")


if __name__ == "__main__":
    app()
