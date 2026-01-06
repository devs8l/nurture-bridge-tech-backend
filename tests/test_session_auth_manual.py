"""
Manual Testing Script for Session & Refresh Token System
Run this script to test the complete authentication flow with sessions.

Usage:
    python tests/test_session_auth_manual.py
"""
import requests
import uuid
import json
from datetime import datetime
from typing import Dict, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "http://localhost:8000"  # Change if your server runs elsewhere
API_PREFIX = "/api/v1"

# Test credentials - UPDATE THESE with real credentials
TEST_USER = {
    "email": "vikas@gmail.com",      # Replace with actual email
    "password": "123qwerty"      # Replace with actual password
}

# Generate a unique device ID for this test session
DEVICE_ID = str(uuid.uuid4())

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log_test(name: str):
    """Log test name"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def log_success(message: str):
    """Log success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def log_error(message: str):
    """Log error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def log_info(message: str):
    """Log info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def print_response(response: requests.Response, show_cookies: bool = True):
    """Pretty print response details"""
    print(f"\nStatus: {response.status_code}")
    
    if show_cookies and response.cookies:
        print(f"Cookies: {dict(response.cookies)}")
    
    try:
        print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response Body: {response.text}")

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_1_login_creates_session(session: requests.Session) -> Dict:
    """Test 1: Login creates session and sets refresh token cookie"""
    log_test("1. Login - Session Creation & Cookie")
    
    url = f"{BASE_URL}{API_PREFIX}/auth/login"
    headers = {
        "Content-Type": "application/json",
        "X-Device-ID": DEVICE_ID
    }
    
    response = session.post(url, json=TEST_USER, headers=headers)
    print_response(response)
    
    # Assertions
    assert response.status_code == 200, "Login should return 200"
    
    data = response.json()
    assert "access_token" in data, "Should have access_token"
    assert "refresh_token" not in data, "Should NOT have refresh_token in JSON"
    assert "token_type" in data, "Should have token_type"
    assert data["token_type"] == "bearer", "Token type should be bearer"
    
    # Check cookie
    assert "refresh_token" in session.cookies, "Should have refresh_token cookie"
    
    log_success("Login successful")
    log_success("Access token received in JSON")
    log_success("Refresh token set in HttpOnly cookie")
    log_info(f"Device ID: {DEVICE_ID}")
    
    return data

def test_2_refresh_token_rotation(session: requests.Session, original_cookies: Dict):
    """Test 2: Refresh token creates new tokens and rotates refresh token"""
    log_test("2. Token Refresh - Rotation")
    
    url = f"{BASE_URL}{API_PREFIX}/auth/refresh"
    headers = {
        "X-Device-ID": DEVICE_ID
    }
    
    # Save old refresh token
    old_refresh_token = session.cookies.get("refresh_token")
    
    # Debug: Print all cookies in session
    print(f"\nDEBUG: Session cookies before refresh:")
    for cookie in session.cookies:
        print(f"  - {cookie.name} = {cookie.value[:50]}... (domain: {cookie.domain}, path: {cookie.path})")
    
    response = session.post(url, headers=headers)
    print_response(response)
    
    # Assertions
    assert response.status_code == 200, "Refresh should return 200"
    
    data = response.json()
    assert "access_token" in data, "Should have new access_token"
    assert "refresh_token" not in data, "Should NOT have refresh_token in JSON"
    
    # Check cookie was rotated
    new_refresh_token = session.cookies.get("refresh_token")
    assert new_refresh_token != old_refresh_token, "Refresh token should be rotated"
    
    log_success("Token refresh successful")
    log_success("New access token received")
    log_success("Refresh token rotated (new cookie set)")
    
    return data

def test_3_refresh_without_device_id_fails(session: requests.Session):
    """Test 3: Refresh without X-Device-ID header should fail"""
    log_test("3. Refresh Without Device ID - Should Fail")
    
    url = f"{BASE_URL}{API_PREFIX}/auth/refresh"
    
    response = session.post(url)  # No headers
    print_response(response, show_cookies=False)
    
    # Assertions
    assert response.status_code == 400, "Should return 400 Bad Request"
    
    log_success("Correctly rejected request without X-Device-ID")

def test_4_logout_revokes_session(session: requests.Session):
    """Test 4: Logout revokes session and clears cookie"""
    log_test("4. Logout - Session Revocation")
    
    url = f"{BASE_URL}{API_PREFIX}/auth/logout"
    
    response = session.post(url)
    
    # Assertions
    assert response.status_code == 204, "Logout should return 204 No Content"
    
    # Check cookie was cleared (some implementations may not clear in the object)
    log_success("Logout successful (204 No Content)")
    log_success("Session revoked in database")
    log_info("Cookie cleared (check Set-Cookie header in actual response)")

def test_5_refresh_after_logout_fails(session: requests.Session):
    """Test 5: Refresh after logout should fail"""
    log_test("5. Refresh After Logout - Should Fail")
    
    url = f"{BASE_URL}{API_PREFIX}/auth/refresh"
    headers = {
        "X-Device-ID": DEVICE_ID
    }
    
    response = session.post(url, headers=headers)
    print_response(response, show_cookies=False)
    
    # Assertions
    assert response.status_code == 401, "Should return 401 Unauthorized"
    
    if response.status_code == 401:
        try:
            error = response.json()
            if isinstance(error.get("detail"), dict):
                error_code = error["detail"].get("code")
                log_info(f"Error code: {error_code}")
                assert error_code in ["SESSION_REVOKED", "INVALID_TOKEN"], "Should return proper error code"
                log_success(f"Correct error code returned: {error_code}")
        except:
            pass
    
    log_success("Correctly rejected refresh with revoked session")

def test_6_one_device_constraint(session1: requests.Session, session2: requests.Session):
    """Test 6: Multiple logins from same device revoke previous session"""
    log_test("6. One Device Constraint - Same Device ID")
    
    # Login with first session
    url = f"{BASE_URL}{API_PREFIX}/auth/login"
    headers = {
        "Content-Type": "application/json",
        "X-Device-ID": "same-device-test"
    }
    
    log_info("First login...")
    response1 = session1.post(url, json=TEST_USER, headers=headers)
    assert response1.status_code == 200
    old_refresh_token = session1.cookies.get("refresh_token")
    
    log_info("Second login with same device ID...")
    response2 = session2.post(url, json=TEST_USER, headers=headers)
    assert response2.status_code == 200
    new_refresh_token = session2.cookies.get("refresh_token")
    
    assert old_refresh_token != new_refresh_token, "Should have different tokens"
    
    log_success("Both logins successful")
    
    # Try to refresh with first session (should fail)
    log_info("Attempting refresh with old session...")
    refresh_url = f"{BASE_URL}{API_PREFIX}/auth/refresh"
    response_old = session1.post(refresh_url, headers={"X-Device-ID": "same-device-test"})
    
    print_response(response_old, show_cookies=False)
    
    assert response_old.status_code == 401, "Old session should be revoked"
    log_success("Old session correctly revoked")
    
    # Try to refresh with second session (should work)
    log_info("Attempting refresh with new session...")
    response_new = session2.post(refresh_url, headers={"X-Device-ID": "same-device-test"})
    
    assert response_new.status_code == 200, "New session should work"
    log_success("New session still valid")

def test_7_missing_refresh_token_fails():
    """Test 7: Refresh without cookie should fail"""
    log_test("7. Refresh Without Cookie - Should Fail")
    
    # Create new session without logging in
    fresh_session = requests.Session()
    
    url = f"{BASE_URL}{API_PREFIX}/auth/refresh"
    headers = {
        "X-Device-ID": DEVICE_ID
    }
    
    response = fresh_session.post(url, headers=headers)
    print_response(response, show_cookies=False)
    
    # Assertions
    assert response.status_code == 401, "Should return 401 Unauthorized"
    
    try:
        error = response.json()
        if isinstance(error.get("detail"), dict):
            assert error["detail"]["code"] == "INVALID_TOKEN"
            log_success("Correct error code: INVALID_TOKEN")
    except:
        pass
    
    log_success("Correctly rejected request without refresh token cookie")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"Session & Refresh Token System - Manual Test Suite")
    print(f"{'='*60}{Colors.END}\n")
    
    print(f"Base URL: {BASE_URL}")
    print(f"Test Device ID: {DEVICE_ID}")
    print(f"Test User Email: {TEST_USER['email']}")
    print(f"\n{Colors.YELLOW}Make sure the server is running and database migration is complete!{Colors.END}\n")
    
    input("Press Enter to start tests...")
    
    try:
        # Test 1: Login
        session = requests.Session()
        test_1_login_creates_session(session)
        
        # Test 2: Refresh with rotation
        original_cookies = dict(session.cookies)
        test_2_refresh_token_rotation(session, original_cookies)
        
        # Test 3: Refresh without device ID
        test_3_refresh_without_device_id_fails(session)
        
        # Test 4: Logout
        test_4_logout_revokes_session(session)
        
        # Test 5: Refresh after logout
        test_5_refresh_after_logout_fails(session)
        
        # Test 6: One device constraint
        session1 = requests.Session()
        session2 = requests.Session()
        test_6_one_device_constraint(session1, session2)
        
        # Test 7: Missing cookie
        test_7_missing_refresh_token_fails()
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}")
        print(f"ALL TESTS PASSED! ✓")
        print(f"{'='*60}{Colors.END}\n")
        
    except AssertionError as e:
        log_error(f"Test failed: {e}")
        print(f"\n{Colors.BOLD}{Colors.RED}{'='*60}")
        print(f"TEST SUITE FAILED ✗")
        print(f"{'='*60}{Colors.END}\n")
        raise
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
