from typing import List, Dict, Any
from .client import ClassroomClient
from .drive_service import DriveService
from .repositories.course_repository import CourseRepository
from .repositories.coursework_repository import CourseworkRepository
from .repositories.submission_repository import SubmissionRepository
from .repositories.student_repository import StudentRepository


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
        submission = self.submission_repository.get_submission_with_student_info(
            course_id, course_work_id, submission_id
        )

        # Add student profile information
        if "userId" in submission:
            student_profile = self.student_repository.get_student_profile(
                submission["userId"]
            )
            submission["studentProfile"] = student_profile

        return submission

    def download_submission_files_with_student_info(
        self,
        course_id: str,
        course_work_id: str,
        submission_id: str,
        download_folder: str = "downloads",
    ) -> Dict[str, Any]:
        """Downloads files and returns information about the student who submitted them."""
        # Get submission with student info
        submission_info = self.get_submission_with_student_info(
            course_id, course_work_id, submission_id
        )

        # Extract student information
        student_name = (
            submission_info.get("studentProfile", {})
            .get("name", {})
            .get("fullName", "Unknown")
        )

        # Download files with student name for folder organization
        attachments = self.get_submission_attachments(
            course_id, course_work_id, submission_id
        )
        downloaded_files = self.drive_service.download_submission_attachments(
            attachments, download_folder, student_name
        )

        return {
            "submission": submission_info,
            "downloaded_files": downloaded_files,
            "student_name": student_name,
            "student_email": submission_info.get("studentProfile", {}).get(
                "emailAddress", "unknown@example.com"
            ),
            "user_id": submission_info.get("userId", "unknown"),
        }
