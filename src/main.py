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
        print(f"📥 Starting download process...")
        print(f"   📋 Course ID: {course_id}")
        print(f"   📝 Assignment ID: {coursework_id}")
        print(f"   📁 Download folder: {download_folder}")

        try:
            coursework_list = service.get_course_work(course_id)
            assignment_title = "Unknown Assignment"
            for work in coursework_list:
                if work.get("id") == coursework_id:
                    assignment_title = work.get("title", "Unknown Assignment")
                    break
            print(f"   📚 Assignment: {assignment_title}")
        except Exception as e:
            print(f"   ⚠️  Could not get assignment title: {e}")

        print(f"\n🔍 Fetching submissions...")
        submissions = service.get_student_submissions(course_id, coursework_id)

        if not submissions:
            print("❌ No submissions found for this assignment.")
            print("   This could mean:")
            print("   - The assignment has no submissions")
            print("   - Invalid assignment ID")
            print("   - Permission issues")
            return

        print(f"✅ Found {len(submissions)} submission(s)")

        # Create base download directory
        from pathlib import Path

        Path(download_folder).mkdir(parents=True, exist_ok=True)

        total_files = 0
        successful_downloads = 0
        students_with_files = 0
        students_without_files = 0
        errors = []

        for i, submission in enumerate(submissions, 1):
            submission_id = submission.get("id")
            user_id = submission.get("userId", "unknown")
            submission_state = submission.get("state", "UNKNOWN")

            if not submission_id:
                print(f"\n[{i}/{len(submissions)}] ⚠️  Skipping submission without ID")
                continue

            try:
                print(f"\n[{i}/{len(submissions)}] Processing submission...")
                print(f"   🆔 Submission ID: {submission_id}")
                print(f"   👤 User ID: {user_id}")
                print(f"   📊 State: {submission_state}")

                result = service.download_submission_files_with_student_info(
                    course_id, coursework_id, submission_id, download_folder
                )

                student_name = result["student_name"]
                student_email = result["student_email"]
                downloaded_files = result["downloaded_files"]

                print(f"   👤 Student: {student_name}")
                print(f"   📧 Email: {student_email}")

                if downloaded_files:
                    print(f"   ✅ Downloaded {len(downloaded_files)} item(s):")
                    for file_path in downloaded_files:
                        file_name = Path(file_path).name
                        print(f"      📄 {file_name}")
                    total_files += len(downloaded_files)
                    successful_downloads += 1
                    students_with_files += 1
                else:
                    print(f"   📝 No files found (directory created)")
                    successful_downloads += 1
                    students_without_files += 1

            except Exception as e:
                error_msg = f"Submission {submission_id} ({user_id}): {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ Error: {e}")

        # Summary
        print(f"\n" + "=" * 60)
        print(f"🎉 Download process completed!")
        print(f"   📊 Total submissions processed: {len(submissions)}")
        print(f"   ✅ Successful downloads: {successful_downloads}")
        print(f"   👥 Students with files: {students_with_files}")
        print(f"   📝 Students without files: {students_without_files}")
        print(f"   📄 Total files/items downloaded: {total_files}")
        print(f"   📁 Files saved to: {Path(download_folder).absolute()}")

        if errors:
            print(f"\n⚠️  Errors encountered ({len(errors)}):")
            for error in errors:
                print(f"   ❌ {error}")

        print(f"\n💡 Tip: Check the download folder for student directories")
        print(f"   Each student has their own folder with their submissions")

    except Exception as e:
        print(f"❌ Critical error in download process: {e}")
        import traceback

        print(f"📋 Full error details:")
        traceback.print_exc()


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
    """Assign a grade to a submission (sets both draft and assigned grade). Uses COURSE_ID from .env if not provided.

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
        # Get student info first
        submission_info = service.get_submission_with_student_info(course_id, coursework_id, submission_id)
        student_name = submission_info.get("studentProfile", {}).get("name", {}).get("fullName", "Unknown")

        print(f"📝 Assigning grade {grade} to {student_name}...")
        service.patch_grade(course_id, coursework_id, submission_id, grade)
        print(f"✅ Grade {grade} assigned successfully to {student_name}")
        print("📊 Both draft and assigned grades have been set")
    except Exception as e:
        print(f"❌ Error assigning grade: {e}")
        print("Note: Grading may require OAuth2 authentication instead of API key.")


@submission_app.command("draft-grade")
def patch_draft_grade(
    coursework_id: str, submission_id: str, grade: float, course_id: str = None
) -> None:
    """Assign a draft grade to a submission (not visible to student). Uses COURSE_ID from .env if not provided."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print("No course ID provided and COURSE_ID not found in environment variables.")
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        submission_info = service.get_submission_with_student_info(course_id, coursework_id, submission_id)
        student_name = submission_info.get("studentProfile", {}).get("name", {}).get("fullName", "Unknown")

        print(f"📝 Assigning draft grade {grade} to {student_name}...")
        service.patch_draft_grade(course_id, coursework_id, submission_id, grade)
        print(f"✅ Draft grade {grade} assigned to {student_name}")
        print("🔒 Grade is saved but not visible to student until returned")

    except Exception as e:
        print(f"❌ Error assigning draft grade: {e}")
        print("Note: Grading may require OAuth2 authentication instead of API key.")


@submission_app.command("assigned-grade")
def patch_assigned_grade(
    coursework_id: str, submission_id: str, grade: float, course_id: str = None
) -> None:
    """Assign a final grade to a submission (visible to student). Uses COURSE_ID from .env if not provided."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print("No course ID provided and COURSE_ID not found in environment variables.")
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        # Get student info first
        submission_info = service.get_submission_with_student_info(course_id, coursework_id, submission_id)
        student_name = submission_info.get("studentProfile", {}).get("name", {}).get("fullName", "Unknown")

        print(f"📝 Assigning final grade {grade} to {student_name}...")
        service.patch_assigned_grade(course_id, coursework_id, submission_id, grade)
        print(f"✅ Final grade {grade} assigned to {student_name}")
        print("👁️  Grade is now visible to student")

    except Exception as e:
        print(f"❌ Error assigning final grade: {e}")
        print("Note: Grading may require OAuth2 authentication instead of API key.")


@submission_app.command("return")
def return_submission(
    coursework_id: str, submission_id: str, course_id: str = None
) -> None:
    """Return a submission to the student (makes grades visible). Uses COURSE_ID from .env if not provided."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print("No course ID provided and COURSE_ID not found in environment variables.")
            return

    client = ClassroomClient()
    service = ClassroomService(client)
    try:
        submission_info = service.get_submission_with_student_info(course_id, coursework_id, submission_id)
        student_name = submission_info.get("studentProfile", {}).get("name", {}).get("fullName", "Unknown")

        print(f"📤 Returning submission from {student_name}...")
        service.return_submission(course_id, coursework_id, submission_id)
        print(f"✅ Submission returned to {student_name}")
        print("👁️  All grades are now visible to student")

    except Exception as e:
        print(f"❌ Error returning submission: {e}")
        print("Note: Returning submissions may require OAuth2 authentication instead of API key.")


@submission_app.command("show-grades")
def show_grades(coursework_id: str, course_id: str = None) -> None:
    """Show current grades for all submissions in an assignment."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print("No course ID provided and COURSE_ID not found in environment variables.")
            return

    client = ClassroomClient()
    service = ClassroomService(client)

    try:
        print(f"📊 Fetching grades for assignment {coursework_id}...")
        submissions = service.get_student_submissions(course_id, coursework_id)

        if not submissions:
            print("❌ No submissions found for this assignment.")
            return

        print(f"📋 Grades for assignment {coursework_id}:")
        print("=" * 80)

        graded_count = 0
        draft_count = 0

        for submission in submissions:
            user_id = submission.get("userId", "unknown")
            assigned_grade = submission.get("assignedGrade")
            draft_grade = submission.get("draftGrade")
            state = submission.get("state", "UNKNOWN")

            try:
                student_profile = service.student_repository.get_student_profile(user_id)
                student_name = student_profile.get("name", {}).get("fullName", f"User_{user_id}")

                print(f"\n👤 {student_name}")
                print(f"   📊 State: {state}")

                if assigned_grade is not None:
                    print(f"   ✅ Assigned Grade: {assigned_grade}")
                    graded_count += 1
                else:
                    print(f"   📝 Assigned Grade: Not graded")

                if draft_grade is not None:
                    print(f"   📄 Draft Grade: {draft_grade}")
                    if assigned_grade is None:
                        draft_count += 1
                else:
                    print(f"   📄 Draft Grade: None")

            except Exception as e:
                print(f"   ❌ Error getting info: {e}")

        print("\n" + "=" * 80)
        print(f"📈 Summary:")
        print(f"   📊 Total submissions: {len(submissions)}")
        print(f"   ✅ Fully graded: {graded_count}")
        print(f"   📄 Draft only: {draft_count}")
        print(f"   ❌ Ungraded: {len(submissions) - graded_count - draft_count}")

    except Exception as e:
        print(f"❌ Error fetching grades: {e}")


@submission_app.command("test-permissions")
def test_permissions(coursework_id: str, course_id: str = None) -> None:
    """Test what permissions we have for the Classroom API."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print("No course ID provided and COURSE_ID not found in environment variables.")
            return

    client = ClassroomClient()
    service = ClassroomService(client)

    print("🔍 Testing API permissions...")
    print(f"   📋 Course ID: {course_id}")
    print(f"   📝 Assignment ID: {coursework_id}")

    try:
        submissions = service.get_student_submissions(course_id, coursework_id)
        print(f"✅ Can read submissions: Found {len(submissions)} submissions")
    except Exception as e:
        print(f"❌ Cannot read submissions: {e}")
        return

    if not submissions:
        print("❌ No submissions found to test grading permissions")
        return

    test_submission = submissions[0]
    submission_id = test_submission.get("id")

    try:
        submission_info = service.get_submission_with_student_info(course_id, coursework_id, submission_id)
        current_assigned = submission_info.get("assignedGrade")
        current_draft = submission_info.get("draftGrade")
        print(f"✅ Can read submission details")
        print(f"   📊 Current assigned grade: {current_assigned}")
        print(f"   📄 Current draft grade: {current_draft}")
    except Exception as e:
        print(f"❌ Cannot read submission details: {e}")
        return

    print("\n🧪 Testing grade modification permissions...")
    try:
        # Try to modify a draft grade
        from repositories.submission_repository import SubmissionRepository
        repo = SubmissionRepository(client)

        test_grade = 85.0
        print(f"   📝 Attempting to set draft grade {test_grade}...")

        repo.patch_draft_grade(course_id, coursework_id, submission_id, test_grade)
        print(f"✅ SUCCESS: Can modify draft grades!")

        # Reset to original grade if there was one
        if current_draft is not None:
            repo.patch_draft_grade(course_id, coursework_id, submission_id, current_draft)
            print(f"   🔄 Restored original draft grade: {current_draft}")

    except Exception as e:
        if "ProjectPermissionDenied" in str(e):
            print(f"❌ PERMISSION DENIED: Your Google Cloud Project lacks permission to modify grades")
            print(f"   📋 Error: {e}")
            print(f"\n💡 Solutions:")
            print(f"   1. Contact Google Workspace admin to enable grading permissions")
            print(f"   2. Use a different Google Cloud Project with approved permissions")
            print(f"   3. Request Google approval for educational use")
        else:
            print(f"❌ Unknown error: {e}")

    # Test 4: Check our current scopes
    print(f"\n🔑 Current OAuth scopes:")
    for scope in client.scopes:
        print(f"   - {scope}")


@submission_app.command("export-grades")
def export_grades(
    coursework_id: str,
    course_id: str = None,
    output_file: str = "grades.csv"
) -> None:
    """Export submission data to CSV for external grading (workaround for permission issues)."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print("No course ID provided and COURSE_ID not found in environment variables.")
            return

    client = ClassroomClient()
    service = ClassroomService(client)

    try:
        print(f"📊 Exporting grades for assignment {coursework_id}...")
        submissions = service.get_student_submissions(course_id, coursework_id)

        if not submissions:
            print("❌ No submissions found for this assignment.")
            return

        # Get assignment info
        try:
            coursework_list = service.get_course_work(course_id)
            assignment_title = "Unknown Assignment"
            for work in coursework_list:
                if work.get("id") == coursework_id:
                    assignment_title = work.get("title", "Unknown Assignment")
                    break
        except Exception:
            assignment_title = "Unknown Assignment"

        import csv
        from pathlib import Path

        # Prepare CSV data
        csv_data = []
        headers = [
            "Student Name", "Email", "User ID", "Submission ID",
            "State", "Assigned Grade", "Draft Grade",
            "Has Attachments", "Submission Time", "Grade to Assign"
        ]

        print(f"📋 Processing {len(submissions)} submissions...")

        for i, submission in enumerate(submissions, 1):
            user_id = submission.get("userId", "unknown")
            submission_id = submission.get("id", "")
            state = submission.get("state", "UNKNOWN")
            assigned_grade = submission.get("assignedGrade", "")
            draft_grade = submission.get("draftGrade", "")
            creation_time = submission.get("creationTime", "")

            try:
                # Get student info
                student_profile = service.student_repository.get_student_profile(user_id)
                student_name = student_profile.get("name", {}).get("fullName", f"User_{user_id}")
                student_email = student_profile.get("emailAddress", "unknown@example.com")

                # Check for attachments
                attachments = service.get_submission_attachments(course_id, coursework_id, submission_id)
                has_attachments = "Yes" if attachments else "No"

                csv_data.append([
                    student_name,
                    student_email,
                    user_id,
                    submission_id,
                    state,
                    assigned_grade,
                    draft_grade,
                    has_attachments,
                    creation_time,
                    ""  # Empty column for manual grade entry
                ])

                print(f"   [{i}/{len(submissions)}] ✅ {student_name}")

            except Exception as e:
                csv_data.append([
                    f"Error_User_{user_id}",
                    "error@unknown.com",
                    user_id,
                    submission_id,
                    state,
                    assigned_grade,
                    draft_grade,
                    "Unknown",
                    creation_time,
                    ""
                ])
                print(f"   [{i}/{len(submissions)}] ⚠️ Error getting info for {user_id}")

        # Write CSV file
        output_path = Path(output_file)
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write metadata
            writer.writerow([f"Assignment: {assignment_title}"])
            writer.writerow([f"Course ID: {course_id}"])
            writer.writerow([f"Assignment ID: {coursework_id}"])
            writer.writerow([])  # Empty row

            # Write headers and data
            writer.writerow(headers)
            writer.writerows(csv_data)

        print(f"\n✅ Export complete!")
        print(f"   📄 File: {output_path.absolute()}")
        print(f"   📊 Students: {len(csv_data)}")
        print(f"\n💡 Instructions:")
        print(f"   1. Open {output_file} in Excel/Google Sheets")
        print(f"   2. Add grades in the 'Grade to Assign' column")
        print(f"   3. Use the data to manually grade in Google Classroom")
        print(f"   4. Or use the import-grades command if permissions are fixed")

    except Exception as e:
        print(f"❌ Error exporting grades: {e}")


@submission_app.command("import-grades")
def import_grades(
    coursework_id: str,
    grades_file: str,
    course_id: str = None,
    dry_run: bool = True
) -> None:
    """Import grades from CSV file (requires grading permissions)."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print("No course ID provided and COURSE_ID not found in environment variables.")
            return

    from pathlib import Path
    import csv

    grades_path = Path(grades_file)
    if not grades_path.exists():
        print(f"❌ Grades file not found: {grades_file}")
        return

    client = ClassroomClient()
    service = ClassroomService(client)

    try:
        print(f"📊 Importing grades from {grades_file}...")
        if dry_run:
            print("🧪 DRY RUN MODE - No actual grades will be assigned")

        # Read CSV file
        grades_to_import = []
        with open(grades_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Skip metadata rows
            for _ in range(4):
                next(csvfile, None)

            reader = csv.DictReader(csvfile)
            for row in reader:
                grade = row.get("Grade to Assign", "").strip()
                if grade and grade != "":
                    try:
                        grade_value = float(grade)
                        grades_to_import.append({
                            "student_name": row.get("Student Name", ""),
                            "submission_id": row.get("Submission ID", ""),
                            "grade": grade_value
                        })
                    except ValueError:
                        print(f"⚠️ Invalid grade '{grade}' for {row.get('Student Name', 'Unknown')}")

        if not grades_to_import:
            print("❌ No valid grades found in CSV file")
            return

        print(f"📋 Found {len(grades_to_import)} grades to import")

        successful = 0
        failed = 0

        for i, grade_data in enumerate(grades_to_import, 1):
            student_name = grade_data["student_name"]
            submission_id = grade_data["submission_id"]
            grade = grade_data["grade"]

            print(f"[{i}/{len(grades_to_import)}] {student_name}: {grade}")

            if not dry_run:
                try:
                    service.patch_grade(course_id, coursework_id, submission_id, grade)
                    successful += 1
                    print(f"   ✅ Grade assigned")
                except Exception as e:
                    failed += 1
                    print(f"   ❌ Failed: {e}")
            else:
                print(f"   🧪 Would assign grade {grade}")

        print(f"\n🎉 Import {'simulation' if dry_run else 'process'} complete!")
        if not dry_run:
            print(f"   ✅ Successful: {successful}")
            print(f"   ❌ Failed: {failed}")
        print(f"   📊 Total: {len(grades_to_import)}")

        if dry_run:
            print(f"\n💡 To actually import grades, run:")
            print(f"   uv run src/main.py submission import-grades {coursework_id} {grades_file} --no-dry-run")

    except Exception as e:
        print(f"❌ Error importing grades: {e}")


@submission_app.command("draft-grade-all")
def draft_grade_all_submissions(
    coursework_id: str,
    grade: float,
    course_id: str = None
) -> None:
    """Assign the same draft grade to all submissions in an assignment."""
    if course_id is None:
        course_id = os.getenv("COURSE_ID")
        if not course_id:
            print("No course ID provided and COURSE_ID not found in environment variables.")
            return

    client = ClassroomClient()
    service = ClassroomService(client)

    try:
        print(f"📝 Draft grading all submissions with grade: {grade}")
        submissions = service.get_student_submissions(course_id, coursework_id)

        if not submissions:
            print("❌ No submissions found for this assignment.")
            return

        successful = 0
        failed = 0

        for i, submission in enumerate(submissions, 1):
            submission_id = submission.get("id")
            user_id = submission.get("userId", "unknown")

            try:
                # Get student name
                student_profile = service.student_repository.get_student_profile(user_id)
                student_name = student_profile.get("name", {}).get("fullName", f"User_{user_id}")

                print(f"[{i}/{len(submissions)}] Draft grading {student_name}...")

                service.patch_draft_grade(course_id, coursework_id, submission_id, grade)
                successful += 1
                print(f"   ✅ Draft grade {grade} assigned")

            except Exception as e:
                failed += 1
                if "ProjectPermissionDenied" in str(e):
                    print(f"   ❌ Permission denied - try 'export-grades' command instead")
                else:
                    print(f"   ❌ Failed: {e}")

        print(f"\n🎉 Bulk draft grading complete!")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Total: {len(submissions)}")

        if failed > 0:
            print(f"\n💡 Alternative: Use 'export-grades' command to export to CSV for manual grading")

    except Exception as e:
        print(f"❌ Error in bulk draft grading: {e}")
        if "ProjectPermissionDenied" in str(e):
            print(f"💡 Try: uv run src/main.py submission export-grades {coursework_id}")


if __name__ == "__main__":
    app()
