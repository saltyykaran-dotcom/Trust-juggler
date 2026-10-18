
import pytest
import cv2
from face_verification import detect_face

@pytest.mark.skipif(not cv2.VideoCapture(0).isOpened(), reason="Webcam not available")


def test_face_detection():
    print("Starting Trust Juggler face detection test...")
    result = detect_face()

    print("\nTest result:")
    print("Success:", result["success"])
    print("Face detected:", result["face_detected"])
    print("Message:", result["message"])


if __name__ == "__main__":
    test_face_detection()
