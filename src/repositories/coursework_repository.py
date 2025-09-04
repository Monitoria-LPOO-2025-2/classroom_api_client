from typing import List, Dict, Any
from ..client import ClassroomClient


class CourseworkRepository:
    """A repository for interacting with Google Classroom coursework."""

    def __init__(self, client: ClassroomClient) -> None:
        self.client: ClassroomClient = client

    def get_course_work(self, course_id: str) -> List[Dict[str, Any]]:
        """Fetches and returns the coursework for a specific course."""
        course_work: Dict[str, Any] = (
            self.client.service.courses()
            .courseWork()
            .list(courseId=course_id)
            .execute()
        )
        return course_work.get("courseWork", [])
