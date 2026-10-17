
def check_access(face_verified):
    """
    Grant protected access only after successful
    face verification.
    """

    if face_verified is True:
        return {
            "access_granted": True,
            "message": "Identity verified. Access granted."
        }

    return {
        "access_granted": False,
        "message": "Identity not verified. Access denied."
    }


if __name__ == "__main__":
    print("Successful verification:")
    print(check_access(True))

    print("\nFailed verification:")
    print(check_access(False))
