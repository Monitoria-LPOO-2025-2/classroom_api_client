from typing import List, Dict, Any
from ..client import ClassroomClient


class StudentRepository:
    """A repository for interacting with Google Classroom students/users."""

    def __init__(self, client: ClassroomClient) -> None:
        self.client: ClassroomClient = client

    def get_student_profile(self, user_id: str) -> Dict[str, Any]:
        """Fetches student profile information by user ID."""
        try:
            profile: Dict[str, Any] = (
                self.client.service.userProfiles().get(userId=user_id).execute()
            )
            return profile
        except Exception as e:
            # If we can't get profile, return basic info
            return {
                "id": user_id,
                "name": {"fullName": f"User {user_id}"},
                "emailAddress": "unknown@example.com",
            }

    def get_course_students(self, course_id: str) -> List[Dict[str, Any]]:
        """Fetches all students enrolled in a course."""
        try:
            students: Dict[str, Any] = (
                self.client.service.courses()
                .students()
                .list(courseId=course_id)
                .execute()
            )
            return students.get("students", [])
        except Exception as e:
            print(f"Error fetching course students: {e}")
            return []
