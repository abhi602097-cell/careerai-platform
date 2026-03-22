"""
middleware/helpers.py
──────────────────────────────────────────────────────────────
Response helpers, validation, and error handling utilities.
"""

from flask import jsonify
from datetime import datetime


def success(data: dict | list, message: str = "Success", status: int = 200):
    """Standard success response wrapper."""
    return jsonify({
        "status":    "success",
        "message":   message,
        "data":      data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }), status


def error(message: str, status: int = 400, details: str = None):
    """Standard error response wrapper."""
    body = {
        "status":    "error",
        "message":   message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if details:
        body["details"] = details
    return jsonify(body), status


def validate_student_input(data: dict) -> list[str]:
    """
    Validate incoming student profile data.
    Returns list of validation error messages (empty = valid).
    """
    errors = []

    # Required fields
    required = ["Gender", "Age", "GPA", "Aptitude_Score", "Degree"]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Range validations
    if "GPA" in data:
        try:
            gpa = float(data["GPA"])
            if not (0 <= gpa <= 4.0):
                errors.append("GPA must be between 0.0 and 4.0")
        except (ValueError, TypeError):
            errors.append("GPA must be a number")

    for gpa_field in ["Math_GPA", "English_GPA", "Science_GPA", "Social_GPA"]:
        if gpa_field in data:
            try:
                val = float(data[gpa_field])
                if not (0 <= val <= 4.0):
                    errors.append(f"{gpa_field} must be between 0.0 and 4.0")
            except (ValueError, TypeError):
                errors.append(f"{gpa_field} must be a number")

    if "Aptitude_Score" in data:
        try:
            apt = int(data["Aptitude_Score"])
            if not (0 <= apt <= 100):
                errors.append("Aptitude_Score must be between 0 and 100")
        except (ValueError, TypeError):
            errors.append("Aptitude_Score must be an integer")

    if "Age" in data:
        try:
            age = int(data["Age"])
            if not (10 <= age <= 60):
                errors.append("Age must be between 10 and 60")
        except (ValueError, TypeError):
            errors.append("Age must be an integer")

    # Enum validations
    if "Gender" in data and data["Gender"] not in ["Male", "Female", "Other"]:
        errors.append("Gender must be 'Male', 'Female', or 'Other'")

    for skill_field in ["Skills_Coding", "Skills_Design", "Skills_Communication",
                        "Skills_Analysis", "Skills_Leadership"]:
        if skill_field in data:
            if data[skill_field] not in [0, 1, "0", "1"]:
                errors.append(f"{skill_field} must be 0 or 1")

    return errors
