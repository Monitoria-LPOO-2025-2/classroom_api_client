from typing import List, Dict, Any
from client import ClassroomClient


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

    def get_all_course_submissions(self, course_id: str) -> List[Dict[str, Any]]:
        """Fetches all submissions for all coursework in a course."""
        from .coursework_repository import CourseworkRepository
        
        coursework_repo = CourseworkRepository(self.client)
        all_coursework = coursework_repo.get_course_work(course_id)
        
        all_submissions = []
        for coursework in all_coursework:
            coursework_id = coursework.get("id")
            if coursework_id:
                try:
                    submissions = self.get_student_submissions(course_id, coursework_id)
                    # Add coursework info to each submission
                    for submission in submissions:
                        submission["coursework"] = {
                            "id": coursework_id,
                            "title": coursework.get("title", "Unknown"),
                            "description": coursework.get("description", ""),
                        }
                    all_submissions.extend(submissions)
                except Exception as e:
                    # Log error but continue with other coursework
                    print(f"Warning: Could not fetch submissions for coursework {coursework_id}: {e}")
                    continue
        
        return all_submissions

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

    def patch_draft_grade(
        self, course_id: str, course_work_id: str, submission_id: str, grade: float
    ) -> None:
        """Assigns only a draft grade to a submission (not visible to student)."""
        body: Dict[str, Any] = {"draftGrade": grade}
        self.client.service.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=course_work_id,
            id=submission_id,
            updateMask="draftGrade",
            body=body,
        ).execute()

    def patch_assigned_grade(
        self, course_id: str, course_work_id: str, submission_id: str, grade: float
    ) -> None:
        """Assigns only a final grade to a submission (visible to student)."""
        body: Dict[str, Any] = {"assignedGrade": grade}
        self.client.service.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=course_work_id,
            id=submission_id,
            updateMask="assignedGrade",
            body=body,
        ).execute()

    def return_submission(
        self, course_id: str, course_work_id: str, submission_id: str
    ) -> None:
        """Returns a submission to the student (makes grades visible)."""
        self.client.service.courses().courseWork().studentSubmissions().return_(
            courseId=course_id,
            courseWorkId=course_work_id,
            id=submission_id
        ).execute()
