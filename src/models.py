from dataclasses import dataclass


@dataclass
class Course:
    """A dataclass to represent a Google Classroom course."""

    id: str
    name: str
    description: str


@dataclass
class CourseWork:
    """A dataclass to represent a Google Classroom coursework."""

    id: str
    title: str
    description: str


@dataclass
class StudentSubmission:
    """A dataclass to represent a student submission."""

    id: str
    user_id: str
    state: str
    assigned_grade: float


@dataclass
class Attachment:
    """A dataclass to represent an attachment."""

    link: str
