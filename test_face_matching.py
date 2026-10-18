
from face_verification import verify_face

rider_id = "test_rider"  # Hardcoded for automated testing

result = verify_face(rider_id)

print("\n--- Trust Juggler Face Verification ---")
print("Success:", result["success"])
print("Verified:", result["verified"])
print("Message:", result["message"])

if "distance" in result:
    print("Matching distance:", result["distance"])
