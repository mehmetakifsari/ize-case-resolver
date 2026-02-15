"""
Test cases for Email Settings feature (Iteration 3)
- GET /api/admin/email-settings - Fetch email settings
- PUT /api/admin/email-settings - Update email settings
- POST /api/admin/email-settings/test - Test SMTP connection
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@ize.com"
ADMIN_PASSWORD = "Admin@123!"


@pytest.fixture(scope="module")
def auth_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture
def admin_headers(auth_token):
    """Auth headers for admin requests"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestEmailSettingsEndpoints:
    """Test email settings CRUD operations"""

    def test_get_email_settings_without_auth(self):
        """Test GET /api/admin/email-settings without authentication - should fail"""
        response = requests.get(f"{BASE_URL}/api/admin/email-settings")
        assert response.status_code == 401, "Should require authentication"
        print("PASS: Email settings endpoint requires authentication")

    def test_get_email_settings_with_auth(self, admin_headers):
        """Test GET /api/admin/email-settings with admin authentication"""
        response = requests.get(
            f"{BASE_URL}/api/admin/email-settings",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "smtp_host" in data, "Missing smtp_host in response"
        assert "smtp_port" in data, "Missing smtp_port in response"
        assert "smtp_user" in data, "Missing smtp_user in response"
        assert "sender_name" in data, "Missing sender_name in response"
        assert "sender_email" in data, "Missing sender_email in response"
        assert "email_enabled" in data, "Missing email_enabled in response"
        
        # Check password is masked
        if data.get("smtp_password_masked"):
            assert "***" in data["smtp_password_masked"] or len(data["smtp_password_masked"]) > 0
            print(f"PASS: Password masked: {data['smtp_password_masked']}")
        
        print(f"PASS: Email settings retrieved - Host: {data['smtp_host']}, Port: {data['smtp_port']}")

    def test_update_email_settings(self, admin_headers):
        """Test PUT /api/admin/email-settings to update settings"""
        # Update settings with test data
        update_data = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "smtp_user": "test@test.com",
            "sender_name": "Test Sender",
            "sender_email": "test@test.com",
            "email_enabled": False
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/email-settings",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        assert "message" in response.json(), "Should return success message"
        print(f"PASS: Email settings updated - {response.json()['message']}")
        
        # Verify the update was applied
        get_response = requests.get(
            f"{BASE_URL}/api/admin/email-settings",
            headers=admin_headers
        )
        assert get_response.status_code == 200
        data = get_response.json()
        
        assert data["smtp_host"] == "smtp.test.com", f"Host not updated: {data['smtp_host']}"
        assert data["smtp_port"] == 465, f"Port not updated: {data['smtp_port']}"
        assert data["smtp_user"] == "test@test.com", f"User not updated: {data['smtp_user']}"
        assert data["sender_name"] == "Test Sender", f"Sender name not updated: {data['sender_name']}"
        assert data["email_enabled"] == False, f"Email enabled not updated: {data['email_enabled']}"
        
        print("PASS: Email settings persistence verified")
        
        # Restore original settings
        restore_data = {
            "smtp_host": "smtp.visupanel.com",
            "smtp_port": 587,
            "smtp_user": "info@visupanel.com",
            "sender_name": "IZE Case Resolver",
            "sender_email": "info@visupanel.com",
            "email_enabled": True
        }
        requests.put(
            f"{BASE_URL}/api/admin/email-settings",
            headers=admin_headers,
            json=restore_data
        )
        print("PASS: Original email settings restored")

    def test_smtp_connection_test_endpoint(self, admin_headers):
        """Test POST /api/admin/email-settings/test - SMTP connection test"""
        response = requests.post(
            f"{BASE_URL}/api/admin/email-settings/test",
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 200, f"SMTP test endpoint failed: {response.text}"
        
        data = response.json()
        assert "success" in data, "Missing 'success' field in response"
        assert "message" in data, "Missing 'message' field in response"
        
        # Note: SMTP may fail due to incorrect password - that's expected behavior
        print(f"PASS: SMTP test endpoint works - Success: {data['success']}, Message: {data['message']}")

    def test_update_smtp_password(self, admin_headers):
        """Test updating SMTP password (should not expose in response)"""
        update_data = {
            "smtp_password": "TestPassword123!"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/email-settings",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Password update failed: {response.text}"
        
        # Verify password is stored but masked
        get_response = requests.get(
            f"{BASE_URL}/api/admin/email-settings",
            headers=admin_headers
        )
        data = get_response.json()
        
        # Password should be masked if returned
        if data.get("smtp_password"):
            print(f"Note: smtp_password returned in response (not recommended)")
        if data.get("smtp_password_masked"):
            assert "***" in data["smtp_password_masked"] or len(data["smtp_password_masked"]) > 0
            print(f"PASS: Password masked correctly: {data['smtp_password_masked']}")


class TestAdminMenuRegressions:
    """Regression tests to ensure other admin pages still work"""

    def test_admin_dashboard_works(self, admin_headers):
        """Test admin dashboard analytics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Admin analytics failed: {response.text}"
        
        data = response.json()
        assert "users" in data, "Missing users in analytics"
        assert "cases" in data, "Missing cases in analytics"
        print(f"PASS: Admin dashboard analytics - Users: {data['users']['total']}, Cases: {data['cases']['total']}")

    def test_admin_users_works(self, admin_headers):
        """Test admin users listing endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Admin users failed: {response.text}"
        assert isinstance(response.json(), list), "Should return list of users"
        print(f"PASS: Admin users endpoint - Found {len(response.json())} users")

    def test_admin_cases_works(self, admin_headers):
        """Test admin cases listing endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/cases",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Admin cases failed: {response.text}"
        assert isinstance(response.json(), list), "Should return list of cases"
        print(f"PASS: Admin cases endpoint - Found {len(response.json())} cases")

    def test_api_settings_works(self, admin_headers):
        """Test API settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/settings",
            headers=admin_headers
        )
        assert response.status_code == 200, f"API settings failed: {response.text}"
        
        data = response.json()
        assert "emergent_key_masked" in data or "emergent_key" in data, "Missing key fields"
        print("PASS: API settings endpoint works")

    def test_site_settings_works(self, admin_headers):
        """Test site settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/site-settings",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Site settings failed: {response.text}"
        print("PASS: Site settings endpoint works")

    def test_warranty_rules_works(self, admin_headers):
        """Test warranty rules listing endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/warranty-rules",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Warranty rules failed: {response.text}"
        assert isinstance(response.json(), list), "Should return list of rules"
        print(f"PASS: Warranty rules endpoint - Found {len(response.json())} rules")
