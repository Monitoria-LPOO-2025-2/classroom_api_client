from typing import List, Dict, Any
from client import ClassroomClient


class CourseRepository:
    """A repository for interacting with Google Classroom courses."""

    def __init__(self, client: ClassroomClient) -> None:
        self.client: ClassroomClient = client

    def get_courses(self) -> List[Dict[str, Any]]:
        """Fetches and returns a list of courses."""
        results: Dict[str, Any] = self.client.service.courses().list().execute()
        return results.get("courses", [])

    def get_course(self, course_id: str) -> Dict[str, Any]:
        """Fetches and returns details of a specific course."""
        return self.client.service.courses().get(id=course_id).execute()
