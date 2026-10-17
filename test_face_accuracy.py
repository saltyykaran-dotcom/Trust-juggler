
from face_verification import verify_face


def main():
    print("=" * 45)
    print(" TRUST JUGGLER - FACE MATCHING EVALUATION")
    print("=" * 45)

    genuine_total = 0
    genuine_accepted = 0

    impostor_total = 0
    impostor_accepted = 0

    print("\nPART 1: GENUINE RIDER TESTS")
    print("Test the enrolled rider against their own face.")
    print("Use separate attempts with normal changes in lighting or angle.")

    try:
        genuine_total = int(
            input("Number of genuine attempts to perform: ")
        )

        if genuine_total < 1:
            print("Enter at least 1 attempt.")
            return

    except ValueError:
        print("Please enter a valid number.")
        return

    for attempt in range(1, genuine_total + 1):
        print(f"\nGenuine attempt {attempt}/{genuine_total}")
        input("Press Enter to open the camera...")

        rider_id = input("Enter the enrolled rider ID: ").strip()
        result = verify_face(rider_id)

        print("Result:", result["message"])

        if result["success"]:
            if result["verified"]:
                genuine_accepted += 1
                print("Outcome: ACCEPTED")
            else:
                print("Outcome: REJECTED")
        else:
            print("Outcome: INVALID TEST —", result["message"])

    print("\nPART 2: DIFFERENT-PERSON TESTS")
    print("Use a consenting test participant who is NOT enrolled")
    print("under the rider ID being tested.")

    try:
        impostor_total = int(
            input("Number of different-person attempts to perform: ")
        )

        if impostor_total < 1:
            print("Enter at least 1 attempt.")
            return

    except ValueError:
        print("Please enter a valid number.")
        return

    for attempt in range(1, impostor_total + 1):
        print(f"\nDifferent-person attempt {attempt}/{impostor_total}")
        rider_id = input(
            "Enter the OTHER person's test target rider ID: "
        ).strip()

        result = verify_face(rider_id)

        print("Result:", result["message"])

        if result["success"]:
            impostor_total_attempted = True
            # Count only completed comparisons.
            if result["verified"]:
                impostor_accepted += 1
                print("Outcome: FALSE ACCEPTANCE")
            else:
                print("Outcome: CORRECT REJECTION")
        else:
            print("Outcome: INVALID TEST —", result["message"])

    print("\n" + "=" * 45)
    print(" EVALUATION SUMMARY")
    print("=" * 45)

    genuine_rate = (
        genuine_accepted / genuine_total * 100
        if genuine_total else 0
    )

    false_acceptance_rate = (
        impostor_accepted / impostor_total * 100
        if impostor_total else 0
    )

    false_rejection_rate = 100 - genuine_rate

    print(f"Genuine acceptance rate: {genuine_rate:.2f}%")
    print(f"False acceptance rate:   {false_acceptance_rate:.2f}%")
    print(f"False rejection rate:    {false_rejection_rate:.2f}%")

    print("\nIMPORTANT:")
    print("These are preliminary prototype measurements.")
    print("Invalid attempts can make the rates misleading.")
    print("Use multiple consenting participants and repeated trials.")
    print("These results are not proof of production-level accuracy.")


if __name__ == "__main__":
    main()
