from typing import List, Dict, Any
from ..client import ClassroomClient


class SubmissionRepository:
    """A repository for interacting with Google Classroom submissions."""

    def __init__(self, client: ClassroomClient) -> None:
        self.client: ClassroomClient = client

    def get_student_submissions(
        self, course_id: str, course_work_id: str
    ) -> List[Dict[str, Any]]:
        """Fetches and returns student submissions for a specific assignment."""
        submissions: Dict[str, Any] = (
            self.client.service.courses()
            .courseWork()
            .studentSubmissions()
            .list(courseId=course_id, courseWorkId=course_work_id)
            .execute()
        )
        return submissions.get("studentSubmissions", [])

    def get_submission_with_student_info(
        self, course_id: str, course_work_id: str, submission_id: str
    ) -> Dict[str, Any]:
        """Fetches a submission with detailed student information."""
        submission: Dict[str, Any] = (
            self.client.service.courses()
            .courseWork()
            .studentSubmissions()
            .get(courseId=course_id, courseWorkId=course_work_id, id=submission_id)
            .execute()
        )
        return submission

    def get_submission_attachments(
        self, course_id: str, course_work_id: str, submission_id: str
    ) -> List[Dict[str, Any]]:
        """Fetches and returns the attachments for a specific submission."""
        submission: Dict[str, Any] = (
            self.client.service.courses()
            .courseWork()
            .studentSubmissions()
            .get(courseId=course_id, courseWorkId=course_work_id, id=submission_id)
            .execute()
        )
        return submission.get("assignmentSubmission", {}).get("attachments", [])

    def add_comment(
        self, course_id: str, course_work_id: str, submission_id: str, comment: str
    ) -> None:
        """Adds a private comment to a submission."""
        body: Dict[str, Any] = {"privateComment": {"text": comment}}
        self.client.service.courses().courseWork().studentSubmissions().modifyAttachments(
            courseId=course_id, courseWorkId=course_work_id, id=submission_id, body=body
        ).execute()

    def patch_grade(
        self, course_id: str, course_work_id: str, submission_id: str, grade: float
    ) -> None:
        """Assigns a grade to a submission."""
        body: Dict[str, Any] = {"assignedGrade": grade, "draftGrade": grade}
        self.client.service.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=course_work_id,
            id=submission_id,
            updateMask="assignedGrade,draftGrade",
            body=body,
        ).execute()
