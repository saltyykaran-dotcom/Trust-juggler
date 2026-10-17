
import cv2
import numpy as np
from pathlib import Path

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

FACE_DIR = Path(__file__).parent / "face_data"
FACE_THRESHOLD = 70


# --------------------------------------------------
# FACE DETECTOR
# --------------------------------------------------

def get_face_detector():
    """Load OpenCV's built-in Haar cascade face detector."""

    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades
        + "haarcascade_frontalface_default.xml"
    )

    if detector.empty():
        raise RuntimeError("Could not load the face detector.")

    return detector


def validate_rider_id(rider_id):
    """Allow only safe characters in rider IDs."""

    rider_id = str(rider_id).strip()

    if not rider_id:
        return False

    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_-"
    )

    return all(char in allowed for char in rider_id)


# --------------------------------------------------
# BASIC FACE DETECTION
# --------------------------------------------------

def detect_face():
    """Open webcam and detect a visible face. Press Q to exit."""

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        return {
            "success": False,
            "face_detected": False,
            "message": "Could not open the webcam."
        }

    try:
        detector = get_face_detector()
        face_detected = False

        while True:
            success, frame = camera.read()

            if not success:
                return {
                    "success": False,
                    "face_detected": False,
                    "message": "Could not read from the webcam."
                }

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(60, 60)
            )

            face_detected = len(faces) > 0

            for (x, y, w, h) in faces:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 200, 0),
                    2
                )

            status = (
                "Face detected"
                if face_detected
                else "No face detected"
            )

            cv2.putText(
                frame,
                status,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 200, 0) if face_detected else (0, 0, 255),
                2
            )

            cv2.imshow("Trust Juggler - Face Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        return {
            "success": True,
            "face_detected": face_detected,
            "message": (
                "Face detected."
                if face_detected
                else "No face detected."
            )
        }

    except Exception as error:
        return {
            "success": False,
            "face_detected": False,
            "message": str(error)
        }

    finally:
        camera.release()
        cv2.destroyAllWindows()


# --------------------------------------------------
# FACE ENROLLMENT
# --------------------------------------------------

def enroll_face(rider_id):
    """
    Capture a face image for an enrolled rider.

    Requires the rider's informed consent.
    Press S to save when exactly one face is visible.
    Press Q to cancel.
    """

    if not validate_rider_id(rider_id):
        return {
            "success": False,
            "message": "Invalid rider ID. Use letters, numbers, _ or -."
        }

    rider_id = str(rider_id).strip()
    FACE_DIR.mkdir(parents=True, exist_ok=True)

    output_path = FACE_DIR / f"{rider_id}.jpg"
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        return {
            "success": False,
            "message": "Could not open the webcam."
        }

    saved = False

    try:
        detector = get_face_detector()

        while True:
            success, frame = camera.read()

            if not success:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(80, 80)
            )

            for (x, y, w, h) in faces:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 200, 0),
                    2
                )

            if len(faces) == 1:
                instruction = "Press S to save face"
                color = (0, 200, 0)
            else:
                instruction = "Show exactly one face clearly"
                color = (0, 0, 255)

            cv2.putText(
                frame,
                instruction,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

            cv2.imshow("Trust Juggler - Face Enrollment", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("s") and len(faces) == 1:
                x, y, w, h = faces[0]
                face_crop = gray[y:y + h, x:x + w]

                saved = cv2.imwrite(
                    str(output_path),
                    face_crop
                )
                break

            if key == ord("q"):
                break

    except Exception as error:
        return {
            "success": False,
            "message": f"Enrollment failed: {error}"
        }

    finally:
        camera.release()
        cv2.destroyAllWindows()

    if saved:
        return {
            "success": True,
            "message": f"Face image saved for rider {rider_id}."
        }

    return {
        "success": False,
        "message": "Enrollment cancelled or face could not be saved."
    }


# --------------------------------------------------
# LIVE FACE MATCHING
# --------------------------------------------------

def verify_face(rider_id, threshold=FACE_THRESHOLD):
    """
    Compare a live face with an enrolled face image using LBPH.

    Lower LBPH distances indicate a closer image match.
    This is an experimental prototype, not secure authentication.
    """

    if not validate_rider_id(rider_id):
        return {
            "success": False,
            "verified": False,
            "message": "Invalid rider ID."
        }

    rider_id = str(rider_id).strip()
    face_path = FACE_DIR / f"{rider_id}.jpg"

    if not face_path.is_file():
        return {
            "success": False,
            "verified": False,
            "message": "No enrolled face found for this rider."
        }

    enrolled_face = cv2.imread(
        str(face_path),
        cv2.IMREAD_GRAYSCALE
    )

    if enrolled_face is None:
        return {
            "success": False,
            "verified": False,
            "message": "Could not read the enrolled face image."
        }

    try:
        detector = get_face_detector()

        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(
            [enrolled_face],
            np.array([0], dtype=np.int32)
        )

    except Exception as error:
        return {
            "success": False,
            "verified": False,
            "message": f"Could not initialize face matching: {error}"
        }

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        return {
            "success": False,
            "verified": False,
            "message": "Could not open the webcam."
        }

    completed = False
    verified = False
    best_distance = None

    try:
        while True:
            success, frame = camera.read()

            if not success:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(80, 80)
            )

            status = "Show exactly one face"
            color = (0, 0, 255)

            if len(faces) == 1:
                x, y, w, h = faces[0]
                live_face = gray[y:y + h, x:x + w]

                live_face = cv2.resize(
                    live_face,
                    (enrolled_face.shape[1], enrolled_face.shape[0])
                )

                _, distance = recognizer.predict(live_face)
                best_distance = float(distance)

                if distance <= threshold:
                    status = f"Possible match: {distance:.1f}"
                    color = (0, 200, 0)
                else:
                    status = f"No match: {distance:.1f}"
                    color = (0, 0, 255)

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    color,
                    2
                )

            cv2.putText(
                frame,
                status,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2
            )

            cv2.putText(
                frame,
                "Press S to accept result | Q to cancel",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

            cv2.imshow("Trust Juggler - Face Verification", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("s") and len(faces) == 1:
                verified = best_distance <= threshold
                completed = True
                break

            if key == ord("q"):
                break

    except Exception as error:
        return {
            "success": False,
            "verified": False,
            "message": f"Verification failed: {error}"
        }

    finally:
        camera.release()
        cv2.destroyAllWindows()

    if not completed:
        return {
            "success": False,
            "verified": False,
            "message": "Verification cancelled or no usable face was available."
        }

    return {
        "success": True,
        "verified": verified,
        "distance": best_distance,
        "message": (
            "Possible face match."
            if verified
            else "Face did not meet the matching threshold."
        )
    }


# --------------------------------------------------
# RUN ENROLLMENT FROM THE TERMINAL
# --------------------------------------------------

if __name__ == "__main__":
    rider_id = input("Enter the registered rider ID: ").strip()

    consent = input(
        "Has the rider consented to face-image storage? (yes/no): "
    ).strip().lower()

    if consent == "yes":
        print(enroll_face(rider_id))
    else:
        print("Enrollment cancelled. Consent is required.")
