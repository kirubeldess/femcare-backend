import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Base URL for the API
BASE_URL = os.getenv("API_URL", "http://localhost:8000")


def test_consultant_invitation_flow():
    """
    Test the complete consultant invitation flow:
    1. Admin logs in
    2. Admin sends invitation to a consultant
    3. Consultant signs up using the invitation link
    4. Verify the consultant role is assigned
    """
    print("=== Testing Consultant Invitation Flow ===")

    # Admin credentials
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "adminpassword")

    # Test consultant email
    consultant_email = "new.consultant@example.com"
    consultant_password = "consultantpassword"
    consultant_name = "Dr. Jane Smith"

    # Step 1: Admin login
    print("\n1. Admin login...")
    login_data = {"username": admin_email, "password": admin_password}

    login_response = requests.post(f"{BASE_URL}/auth/token", data=login_data)

    if login_response.status_code != 200:
        print(f"Admin login failed: {login_response.text}")
        return

    admin_token = login_response.json()["access_token"]
    print(f"Admin login successful. Token received.")

    # Step 2: Admin sends invitation
    print("\n2. Sending consultant invitation...")

    # Signup link with role parameter
    signup_link = f"{BASE_URL}/mobile/signup?email={consultant_email}&role=consultant"

    invite_data = {"email": consultant_email, "signup_link": signup_link}

    invite_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }

    invite_response = requests.post(
        f"{BASE_URL}/consultants/send-invite", json=invite_data, headers=invite_headers
    )

    if invite_response.status_code != 200:
        print(f"Invitation failed: {invite_response.text}")
        return

    print(f"Invitation sent successfully: {invite_response.json()['message']}")
    print(f"Signup link: {signup_link}")

    # Step 3: Consultant signs up
    print("\n3. Consultant signing up...")

    signup_data = {
        "name": consultant_name,
        "email": consultant_email,
        "password": consultant_password,
        "phone": "1234567890",
        "language": "en",
    }

    # The role parameter is included in the URL query string
    signup_response = requests.post(
        f"{BASE_URL}/auth/signup?role=consultant", json=signup_data
    )

    if signup_response.status_code != 201:
        print(f"Consultant signup failed: {signup_response.text}")
        return

    print(
        f"Consultant signup successful: {json.dumps(signup_response.json(), indent=2)}"
    )

    # Step 4: Consultant logs in to verify role
    print("\n4. Consultant logging in to verify role...")

    consultant_login_data = {
        "username": consultant_email,
        "password": consultant_password,
    }

    consultant_login_response = requests.post(
        f"{BASE_URL}/auth/token", data=consultant_login_data
    )

    if consultant_login_response.status_code != 200:
        print(f"Consultant login failed: {consultant_login_response.text}")
        return

    consultant_token = consultant_login_response.json()["access_token"]

    # Get consultant profile
    me_headers = {"Authorization": f"Bearer {consultant_token}"}

    me_response = requests.get(f"{BASE_URL}/auth/me", headers=me_headers)

    if me_response.status_code != 200:
        print(f"Failed to get consultant profile: {me_response.text}")
        return

    consultant_profile = me_response.json()
    print(f"Consultant profile retrieved:")
    print(f"Name: {consultant_profile['name']}")
    print(f"Email: {consultant_profile['email']}")
    print(f"Role: {consultant_profile['role']}")

    if consultant_profile["role"] == "consultant":
        print("\n✅ Success! Consultant role was correctly assigned.")
    else:
        print(
            f"\n❌ Error: Consultant role was not assigned. Current role: {consultant_profile['role']}"
        )


if __name__ == "__main__":
    test_consultant_invitation_flow()
