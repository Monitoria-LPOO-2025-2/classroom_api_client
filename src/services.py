from typing import List, Dict, Any
from client import ClassroomClient
from drive_service import DriveService
from repositories.course_repository import CourseRepository
from repositories.coursework_repository import CourseworkRepository
from repositories.submission_repository import SubmissionRepository
from repositories.student_repository import StudentRepository


class ClassroomService:
    """A service for interacting with Google Classroom data."""

    def __init__(self, client: ClassroomClient) -> None:
        self.client: ClassroomClient = client
        self.course_repository: CourseRepository = CourseRepository(client)
        self.coursework_repository: CourseworkRepository = CourseworkRepository(client)
        self.submission_repository: SubmissionRepository = SubmissionRepository(client)
        self.student_repository: StudentRepository = StudentRepository(client)
        self.drive_service: DriveService = DriveService(client)

    def get_courses(self) -> List[Dict[str, Any]]:
        """Fetches and returns a list of courses."""
        return self.course_repository.get_courses()

    def get_course(self, course_id: str) -> Dict[str, Any]:
        """Fetches and returns details of a specific course."""
        return self.course_repository.get_course(course_id)

    def get_course_work(self, course_id: str) -> List[Dict[str, Any]]:
        """Fetches and returns the coursework for a specific course."""
        return self.coursework_repository.get_course_work(course_id)

    def get_student_submissions(
        self, course_id: str, course_work_id: str
    ) -> List[Dict[str, Any]]:
        """Fetches and returns student submissions for a specific assignment."""
        return self.submission_repository.get_student_submissions(
            course_id, course_work_id
        )

    def resolve_course_id(self, course_identifier: str) -> str:
        """Resolve a course ID given either an ID or (case-insensitive) name fragment.

        If the identifier matches an existing course id exactly, return it.
        Otherwise perform a case-insensitive containment match against course names.
        Raises ValueError if not found or ambiguous.
        """
        from repositories.course_repository import CourseRepository

        client = self.client
        repo = CourseRepository(client)
        courses = repo.get_courses()

        for c in courses:
            if c.get("id") == course_identifier:
                return course_identifier

        ci = course_identifier.lower()
        matches = [c for c in courses if ci in c.get("name", "").lower()]
        if not matches:
            raise ValueError(f"No course found matching '{course_identifier}'")
        if len(matches) > 1:
            names = ", ".join(f"{c.get('name')} ({c.get('id')})" for c in matches[:6])
            if len(matches) > 6:
                names += ", ..."
            raise ValueError(
                f"Ambiguous course identifier '{course_identifier}'. Matches: {names}"
            )
        return matches[0].get("id")

    def resolve_coursework_id(self, course_id: str, work_identifier: str) -> str:
        """Resolve a coursework ID given either an ID or name fragment inside a course.

        Strategy mirrors resolve_course_id.
        """
        from repositories.coursework_repository import CourseworkRepository

        repo = CourseworkRepository(self.client)
        work_list = repo.get_course_work(course_id)

        # Exact id match
        for w in work_list:
            if w.get("id") == work_identifier:
                return work_identifier

        wi = work_identifier.lower()
        matches = [w for w in work_list if wi in w.get("title", "").lower()]
        if not matches:
            raise ValueError(
                f"No coursework found in course {course_id} matching '{work_identifier}'"
            )
        if len(matches) > 1:
            names = ", ".join(f"{w.get('title')} ({w.get('id')})" for w in matches[:6])
            if len(matches) > 6:
                names += ", ..."
            raise ValueError(
                f"Ambiguous coursework identifier '{work_identifier}'. Matches: {names}"
            )
        return matches[0].get("id")

    def get_submission_attachments(
        self, course_id: str, course_work_id: str, submission_id: str
    ) -> List[Dict[str, Any]]:
        """Fetches and returns the attachments for a specific submission."""
        return self.submission_repository.get_submission_attachments(
            course_id, course_work_id, submission_id
        )

    def add_comment(
        self, course_id: str, course_work_id: str, submission_id: str, comment: str
    ) -> None:
        """Adds a private comment to a submission."""
        self.submission_repository.add_comment(
            course_id, course_work_id, submission_id, comment
        )

    def patch_grade(
        self, course_id: str, course_work_id: str, submission_id: str, grade: float
    ) -> None:
        """Assigns a grade to a submission."""
        self.submission_repository.patch_grade(
            course_id, course_work_id, submission_id, grade
        )

    def patch_draft_grade(
        self, course_id: str, course_work_id: str, submission_id: str, grade: float
    ) -> None:
        """Assigns only a draft grade to a submission (not visible to student)."""
        self.submission_repository.patch_draft_grade(
            course_id, course_work_id, submission_id, grade
        )

    def patch_assigned_grade(
        self, course_id: str, course_work_id: str, submission_id: str, grade: float
    ) -> None:
        """Assigns only a final grade to a submission (visible to student)."""
        self.submission_repository.patch_assigned_grade(
            course_id, course_work_id, submission_id, grade
        )

    def return_submission(
        self, course_id: str, course_work_id: str, submission_id: str
    ) -> None:
        """Returns a submission to the student (makes grades visible)."""
        self.submission_repository.return_submission(
            course_id, course_work_id, submission_id
        )

    def download_submission_files(
        self,
        course_id: str,
        course_work_id: str,
        submission_id: str,
        download_folder: str = "downloads",
    ) -> List[str]:
        """Downloads all files attached to a submission."""
        attachments = self.get_submission_attachments(
            course_id, course_work_id, submission_id
        )
        return self.drive_service.download_submission_attachments(
            attachments, download_folder
        )

    def get_submission_with_student_info(
        self, course_id: str, course_work_id: str, submission_id: str
    ) -> Dict[str, Any]:
        """Gets submission details including student information."""
        try:
            submission = self.submission_repository.get_submission_with_student_info(
                course_id, course_work_id, submission_id
            )

            # Add student profile information
            if "userId" in submission:
                try:
                    student_profile = self.student_repository.get_student_profile(
                        submission["userId"]
                    )
                    submission["studentProfile"] = student_profile
                except Exception as e:
                    print(
                        f"⚠️  Warning: Could not get student profile for user {submission['userId']}: {e}"
                    )
                    # Create a minimal profile
                    submission["studentProfile"] = {
                        "id": submission["userId"],
                        "name": {"fullName": f"User_{submission['userId']}"},
                        "emailAddress": f"user_{submission['userId']}@unknown.com",
                    }

            return submission

        except Exception as e:
            print(f"❌ Error getting submission info: {e}")
            # Return minimal submission info
            return {
                "id": submission_id,
                "userId": "unknown",
                "state": "UNKNOWN",
                "studentProfile": {
                    "id": "unknown",
                    "name": {"fullName": "Unknown Student"},
                    "emailAddress": "unknown@unknown.com",
                },
            }

    def download_submission_files_with_student_info(
        self,
        course_id: str,
        course_work_id: str,
        submission_id: str,
        download_folder: str = "downloads",
    ) -> Dict[str, Any]:
        """Downloads files and returns information about the student who submitted them."""
        try:
            # Get submission with student info
            submission_info = self.get_submission_with_student_info(
                course_id, course_work_id, submission_id
            )

            # Extract student information with better fallbacks
            student_profile = submission_info.get("studentProfile", {})

            student_name = (
                student_profile.get("name", {}).get("fullName")
                or student_profile.get("name", {}).get("givenName", "")
                + " "
                + student_profile.get("name", {}).get("familyName", "")
                or f"Student_{submission_info.get('userId', 'Unknown')}"
            ).strip()

            if not student_name or student_name == "Student_":
                student_name = f"Student_{submission_info.get('userId', 'Unknown')}"

            student_email = (
                student_profile.get("emailAddress")
                or f"student_{submission_info.get('userId', 'unknown')}@unknown.com"
            )

            print(f"👤 Student identified: {student_name}")
            print(f"📧 Email: {student_email}")

            # Get all attachments for this submission
            attachments = self.get_submission_attachments(
                course_id, course_work_id, submission_id
            )

            print(f"🔍 Found {len(attachments)} attachment(s) in submission")

            # Download files with student name for folder organization
            downloaded_files = self.drive_service.download_submission_attachments(
                attachments, download_folder, student_name
            )

            return {
                "submission": submission_info,
                "downloaded_files": downloaded_files,
                "student_name": student_name,
                "student_email": student_email,
                "user_id": submission_info.get("userId", "unknown"),
                "submission_state": submission_info.get("state", "UNKNOWN"),
                "attachments_count": len(attachments),
            }

        except Exception as e:
            print(f"❌ Error in download_submission_files_with_student_info: {e}")
            # Return minimal info even on error
            return {
                "submission": {"id": submission_id, "userId": "unknown"},
                "downloaded_files": [],
                "student_name": f"Error_Student_{submission_id[:8]}",
                "student_email": "error@unknown.com",
                "user_id": "unknown",
                "submission_state": "ERROR",
                "attachments_count": 0,
                "error": str(e),
            }
