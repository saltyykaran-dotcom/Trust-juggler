
import cv2
import numpy as np
from pathlib import Path
import time

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
FACE_DIR = BASE_DIR / "face_data"

FACE_THRESHOLD = 70

# Optional local copy of the Haar Cascade XML file.
LOCAL_CASCADE = BASE_DIR / "haarcascade_frontalface_default.xml"

CAMERA_INDEXES = (0, 1, 2)
CAMERA_BACKENDS = (
    cv2.CAP_DSHOW,
    cv2.CAP_MSMF,
    cv2.CAP_ANY,
)


# --------------------------------------------------
# WEBCAM INITIALIZATION
# --------------------------------------------------

def open_camera():
    """Try multiple Windows camera indexes and backends."""

    for index in CAMERA_INDEXES:
        for backend in CAMERA_BACKENDS:
            camera = None

            try:
                camera = cv2.VideoCapture(index, backend)

                if not camera.isOpened():
                    camera.release()
                    continue

                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

                # Read several frames while the camera initializes.
                for _ in range(10):
                    success, frame = camera.read()

                    if success and frame is not None and frame.size > 0:
                        print(
                            f"Webcam opened: index={index}, "
                            f"backend={backend}"
                        )
                        return camera

                    time.sleep(0.1)

                camera.release()

            except Exception as error:
                print(
                    f"Camera attempt failed: index={index}, "
                    f"backend={backend}: {error}"
                )

                if camera is not None:
                    camera.release()

    return None


def read_camera_frame(camera):
    """Read one valid frame from the webcam."""

    try:
        success, frame = camera.read()

        if success and frame is not None and frame.size > 0:
            return frame

    except Exception:
        pass

    return None


def close_camera(camera):
    """Release the webcam and close OpenCV windows."""

    if camera is not None:
        try:
            camera.release()
        except Exception:
            pass

    try:
        cv2.destroyAllWindows()
    except Exception:
        pass


# --------------------------------------------------
# FACE DETECTOR
# --------------------------------------------------

def get_face_detector():
    """
    Load the Haar Cascade detector.

    Checks the project folder first, then OpenCV's installed
    cascade directory. Raises a useful error if neither works.
    """

    candidates = [
        LOCAL_CASCADE,
        Path(cv2.data.haarcascades)
        / "haarcascade_frontalface_default.xml",
    ]

    checked_paths = []

    for cascade_path in candidates:
        cascade_path = Path(cascade_path).resolve()

        # Avoid checking the same file twice.
        if cascade_path in checked_paths:
            continue

        checked_paths.append(cascade_path)

        if not cascade_path.is_file():
            continue

        try:
            detector = cv2.CascadeClassifier(str(cascade_path))

            if not detector.empty():
                print(f"Face detector loaded: {cascade_path}")
                return detector

        except Exception as error:
            print(f"Could not load {cascade_path}: {error}")

    paths = "\n".join(str(path) for path in checked_paths)

    raise RuntimeError(
        "Could not load the Haar Cascade face detector.\n"
        f"OpenCV version: {cv2.__version__}\n"
        f"Checked paths:\n{paths}\n"
        "Download haarcascade_frontalface_default.xml from "
        "the official OpenCV repository and place it beside "
        "face_verification.py."
    )


# --------------------------------------------------
# RIDER ID VALIDATION
# --------------------------------------------------

def validate_rider_id(rider_id):
    """Allow only letters, numbers, underscores and hyphens."""

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
# FACE DETECTION HELPER
# --------------------------------------------------

def detect_faces(detector, frame, min_size=(60, 60)):
    """Return a grayscale frame and detected face coordinates."""

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=min_size
    )

    return gray, faces


# --------------------------------------------------
# BASIC FACE DETECTION
# --------------------------------------------------

def detect_face():
    """Detect faces through the webcam. Press Q to exit."""

    camera = open_camera()

    if camera is None:
        return {
            "success": False,
            "face_detected": False,
            "message": (
                "Could not open the webcam. Check Windows camera "
                "permissions and close other camera applications."
            )
        }

    face_detected = False

    try:
        detector = get_face_detector()

        while True:
            frame = read_camera_frame(camera)

            if frame is None:
                return {
                    "success": False,
                    "face_detected": False,
                    "message": "Could not read a frame from the webcam."
                }

            _, faces = detect_faces(detector, frame)
            face_detected = len(faces) > 0

            for x, y, w, h in faces:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 200, 0),
                    2
                )

            status = (
                "Face detected" if face_detected
                else "No face detected"
            )
            color = (0, 200, 0) if face_detected else (0, 0, 255)

            cv2.putText(
                frame,
                status,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2
            )

            cv2.putText(
                frame,
                "Press Q to exit",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
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
            "message": f"Face detection failed: {error}"
        }

    finally:
        close_camera(camera)


# --------------------------------------------------
# FACE ENROLLMENT
# --------------------------------------------------

def enroll_face(rider_id):
    """
    Capture and store a face image.

    The calling application must obtain informed consent before
    calling this function.

    Press S to save when exactly one face is visible.
    Press Q to cancel.
    """

    if not validate_rider_id(rider_id):
        return {
            "success": False,
            "message": "Invalid rider ID. Use letters, numbers, _ or -."
        }

    rider_id = str(rider_id).strip()
    output_path = FACE_DIR / f"{rider_id}.jpg"

    if output_path.exists():
        return {
            "success": False,
            "message": (
                "A face image is already enrolled for this rider. "
                "Use an authorized replacement or deletion workflow "
                "before enrolling again."
            )
        }

    # Load the detector before opening the camera.
    try:
        detector = get_face_detector()
    except Exception as error:
        return {
            "success": False,
            "message": f"Enrollment failed: {error}"
        }

    camera = open_camera()

    if camera is None:
        return {
            "success": False,
            "message": (
                "Could not open the webcam. Check Windows camera "
                "permissions and close other camera applications."
            )
        }

    saved = False

    try:
        while True:
            frame = read_camera_frame(camera)

            if frame is None:
                return {
                    "success": False,
                    "message": "Could not read from the webcam."
                }

            gray, faces = detect_faces(
                detector,
                frame,
                min_size=(80, 80)
            )

            for x, y, w, h in faces:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 200, 0),
                    2
                )

            if len(faces) == 1:
                instruction = "Press S to save | Q to cancel"
                color = (0, 200, 0)
            else:
                instruction = "Show exactly one face | Q to cancel"
                color = (0, 0, 255)

            cv2.putText(
                frame,
                instruction,
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2
            )

            cv2.imshow("Trust Juggler - Face Enrollment", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("s") and len(faces) == 1:
                x, y, w, h = faces[0]
                face_crop = gray[y:y + h, x:x + w]

                if face_crop.size == 0:
                    continue

                FACE_DIR.mkdir(parents=True, exist_ok=True)

                saved = cv2.imwrite(
                    str(output_path),
                    face_crop
                )

                if not saved:
                    return {
                        "success": False,
                        "message": "Could not save the face image."
                    }

                break

            if key == ord("q"):
                break

        if saved:
            return {
                "success": True,
                "message": f"Face image saved for rider {rider_id}."
            }

        return {
            "success": False,
            "message": "Enrollment cancelled. No image was saved."
        }

    except Exception as error:
        # Remove an incomplete image, but preserve a valid saved image.
        if not saved:
            try:
                if output_path.exists() and output_path.stat().st_size == 0:
                    output_path.unlink()
            except OSError:
                pass

        return {
            "success": False,
            "message": f"Enrollment failed: {error}"
        }

    finally:
        close_camera(camera)


# --------------------------------------------------
# LIVE FACE MATCHING
# --------------------------------------------------

def verify_face(rider_id, threshold=FACE_THRESHOLD):
    """
    Compare a live face against the enrolled image using LBPH.

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

    if enrolled_face is None or enrolled_face.size == 0:
        return {
            "success": False,
            "verified": False,
            "message": "Could not read the enrolled face image."
        }

    try:
        if not hasattr(cv2, "face"):
            return {
                "success": False,
                "verified": False,
                "message": (
                    "LBPH is unavailable. Install "
                    "opencv-contrib-python in the active environment."
                )
            }

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

    camera = open_camera()

    if camera is None:
        return {
            "success": False,
            "verified": False,
            "message": (
                "Could not open the webcam. Check camera permissions "
                "and close other camera applications."
            )
        }

    completed = False
    verified = False
    best_distance = None

    try:
        while True:
            frame = read_camera_frame(camera)

            if frame is None:
                return {
                    "success": False,
                    "verified": False,
                    "message": "Could not read from the webcam."
                }

            gray, faces = detect_faces(
                detector,
                frame,
                min_size=(80, 80)
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

                if best_distance <= threshold:
                    status = f"Possible match: {best_distance:.1f}"
                    color = (0, 200, 0)
                else:
                    status = f"No match: {best_distance:.1f}"
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
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2
            )

            cv2.putText(
                frame,
                "Press S to accept result | Q to cancel",
                (15, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )

            cv2.imshow("Trust Juggler - Face Verification", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("s") and len(faces) == 1:
                verified = (
                    best_distance is not None
                    and best_distance <= threshold
                )
                completed = True
                break

            if key == ord("q"):
                break

        if not completed:
            return {
                "success": False,
                "verified": False,
                "message": (
                    "Verification cancelled or no usable face "
                    "was available."
                )
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

    except Exception as error:
        return {
            "success": False,
            "verified": False,
            "message": f"Verification failed: {error}"
        }

    finally:
        close_camera(camera)


# --------------------------------------------------
# RUN ENROLLMENT FROM THE TERMINAL
# --------------------------------------------------

if __name__ == "__main__":
    rider_id = input("Enter the registered rider ID: ").strip()

    consent = input(
        "Has the rider given informed consent to capture "
        "and store their face image? (yes/no): "
    ).strip().lower()

    if consent == "yes":
        print(enroll_face(rider_id))
    else:
        print("Enrollment cancelled. Consent is required.")
