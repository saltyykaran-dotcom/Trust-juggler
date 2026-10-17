
import json
from pathlib import Path

ENROLLMENT_FILE = Path(__file__).parent / "data" / "face_enrollments.json"


def save_enrollment(rider_id, image_filename):
    """Save the filename associated with a rider's face enrollment."""

    ENROLLMENT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if ENROLLMENT_FILE.exists():
        with open(ENROLLMENT_FILE, "r", encoding="utf-8") as file:
            enrollments = json.load(file)
    else:
        enrollments = {}

    enrollments[rider_id] = {
        "image_filename": image_filename,
        "enrolled": True
    }

    with open(ENROLLMENT_FILE, "w", encoding="utf-8") as file:
        json.dump(enrollments, file, indent=4)

    return True


def get_enrollment(rider_id):
    """Return saved enrollment metadata, if present."""

    if not ENROLLMENT_FILE.exists():
        return None

    with open(ENROLLMENT_FILE, "r", encoding="utf-8") as file:
        enrollments = json.load(file)

    return enrollments.get(rider_id)
