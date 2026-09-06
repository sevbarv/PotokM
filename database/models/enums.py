from enum import Enum


class UserRole(str, Enum):
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"
    EMPLOYEE = "employee"
