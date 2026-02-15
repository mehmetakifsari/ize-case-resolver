"""
IZE Case Resolver API Tests
- Authentication: register, login, password validation
- Admin endpoints: analytics, users, cases
- User roles and permissions
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://pdf-analyzer-78.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "admin@ize.com"
ADMIN_PASSWORD = "Admin@123!"
TEST_USER_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "Test@123!"
TEST_USER_FULLNAME = "Test User"


class TestAPIRoot:
    """Root API endpoint tests"""
    
    def test_api_root(self):
        """Test API root endpoint returns success"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "IZE Case Resolver API"
        assert data["version"] == "2.0"
        print("✓ API root endpoint working")

    def test_branches_endpoint(self):
        """Test branches endpoint returns valid branches"""
        response = requests.get(f"{BASE_URL}/api/branches")
        assert response.status_code == 200
        data = response.json()
        assert "branches" in data
        expected_branches = ["Bursa", "İzmit", "Orhanlı", "Hadımköy", "Keşan"]
        assert data["branches"] == expected_branches
        print("✓ Branches endpoint working")


class TestAuthRegister:
    """User registration tests with password validation"""
    
    def test_register_success(self):
        """Test successful user registration with valid data"""
        unique_email = f"test_reg_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "ValidPass@123",
            "full_name": "Test Registration User",
            "phone_number": "5551234567",
            "branch": "Bursa",
            "role": "user"
        })
        assert response.status_code == 200, f"Register failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == unique_email
        assert data["user"]["full_name"] == "Test Registration User"
        assert data["user"]["phone_number"] == "5551234567"
        assert data["user"]["branch"] == "Bursa"
        assert data["user"]["free_analyses_remaining"] == 5
        print("✓ User registration successful")
        return data["access_token"]

    def test_register_duplicate_email(self):
        """Test registration fails with duplicate email"""
        # First register
        unique_email = f"test_dup_{uuid.uuid4().hex[:8]}@example.com"
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "ValidPass@123",
            "full_name": "First User"
        })
        # Try duplicate
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "ValidPass@123",
            "full_name": "Second User"
        })
        assert response.status_code == 400
        assert "zaten kayıtlı" in response.json()["detail"].lower()
        print("✓ Duplicate email rejected correctly")

    def test_register_password_too_short(self):
        """Test password must be at least 8 characters"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_short_{uuid.uuid4().hex[:8]}@example.com",
            "password": "Ab@1",
            "full_name": "Short Pass User"
        })
        assert response.status_code == 422
        print("✓ Short password rejected correctly")

    def test_register_password_no_uppercase(self):
        """Test password must contain uppercase letter"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_nouc_{uuid.uuid4().hex[:8]}@example.com",
            "password": "lowercase@123",
            "full_name": "No Uppercase User"
        })
        assert response.status_code == 422
        print("✓ Password without uppercase rejected")

    def test_register_password_no_lowercase(self):
        """Test password must contain lowercase letter"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_nolc_{uuid.uuid4().hex[:8]}@example.com",
            "password": "UPPERCASE@123",
            "full_name": "No Lowercase User"
        })
        assert response.status_code == 422
        print("✓ Password without lowercase rejected")

    def test_register_password_no_special_char(self):
        """Test password must contain special character"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_nosp_{uuid.uuid4().hex[:8]}@example.com",
            "password": "NoSpecial123",
            "full_name": "No Special Char User"
        })
        assert response.status_code == 422
        print("✓ Password without special char rejected")

    def test_register_invalid_branch(self):
        """Test registration fails with invalid branch"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_branch_{uuid.uuid4().hex[:8]}@example.com",
            "password": "ValidPass@123",
            "full_name": "Invalid Branch User",
            "branch": "InvalidBranch"
        })
        assert response.status_code == 422
        print("✓ Invalid branch rejected correctly")


class TestAuthLogin:
    """User login tests"""

    def test_login_admin_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        print("✓ Admin login successful")
        return data["access_token"]

    def test_login_invalid_password(self):
        """Test login fails with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "WrongPassword@123"
        })
        assert response.status_code == 401
        assert "hatalı" in response.json()["detail"].lower()
        print("✓ Invalid password rejected correctly")

    def test_login_nonexistent_user(self):
        """Test login fails for non-existent user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "AnyPass@123"
        })
        assert response.status_code == 401
        print("✓ Non-existent user rejected correctly")


class TestAuthMe:
    """Current user endpoint tests"""
    
    def test_me_without_token(self):
        """Test /auth/me fails without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 403
        print("✓ Unauthorized access rejected")

    def test_me_with_token(self):
        """Test /auth/me returns user info with valid token"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Get user info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "admin"
        print("✓ Auth me endpoint working")


class TestAdminAnalytics:
    """Admin analytics endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_analytics_unauthorized(self):
        """Test analytics requires admin token"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code == 403
        print("✓ Analytics unauthorized access rejected")

    def test_analytics_with_admin(self, admin_token):
        """Test admin can access analytics"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "cases" in data
        assert "branches" in data
        assert "decisions" in data
        assert data["users"]["total"] >= 0
        print("✓ Admin analytics endpoint working")


class TestAdminUsers:
    """Admin user management tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]

    def test_list_users(self, admin_token):
        """Test admin can list all users"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) > 0
        # Check user structure
        user = users[0]
        assert "id" in user
        assert "email" in user
        assert "full_name" in user
        assert "hashed_password" not in user  # Should be excluded
        print(f"✓ Listed {len(users)} users")

    def test_filter_users_by_branch(self, admin_token):
        """Test admin can filter users by branch"""
        response = requests.get(f"{BASE_URL}/api/admin/users?branch=Bursa", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        users = response.json()
        for user in users:
            if user.get("branch"):
                assert user["branch"] == "Bursa"
        print("✓ Branch filter working")

    def test_filter_users_by_role(self, admin_token):
        """Test admin can filter users by role"""
        response = requests.get(f"{BASE_URL}/api/admin/users?role=admin", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        users = response.json()
        for user in users:
            assert user["role"] == "admin"
        print("✓ Role filter working")

    def test_add_credit_to_user(self, admin_token):
        """Test admin can add credit to a user"""
        # First create a test user
        unique_email = f"test_credit_{uuid.uuid4().hex[:8]}@example.com"
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "CreditTest@123",
            "full_name": "Credit Test User"
        })
        user_id = reg_response.json()["user"]["id"]
        initial_credit = reg_response.json()["user"]["free_analyses_remaining"]
        
        # Add credit
        response = requests.patch(f"{BASE_URL}/api/admin/users/{user_id}/add-credit?amount=5", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["new_balance"] == initial_credit + 5
        print("✓ Credit addition working")


class TestAdminCases:
    """Admin cases management tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]

    def test_list_all_cases(self, admin_token):
        """Test admin can list all cases"""
        response = requests.get(f"{BASE_URL}/api/admin/cases", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        cases = response.json()
        assert isinstance(cases, list)
        print(f"✓ Listed {len(cases)} cases")

    def test_filter_cases_by_branch(self, admin_token):
        """Test admin can filter cases by branch"""
        response = requests.get(f"{BASE_URL}/api/admin/cases?branch=Bursa", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        cases = response.json()
        for case in cases:
            if case.get("branch"):
                assert case["branch"] == "Bursa"
        print("✓ Cases branch filter working")


class TestUserCases:
    """User cases endpoint tests"""
    
    @pytest.fixture
    def user_token(self):
        """Create and get user token"""
        unique_email = f"test_cases_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "CasesTest@123",
            "full_name": "Cases Test User"
        })
        return response.json()["access_token"]

    def test_user_get_own_cases(self, user_token):
        """Test user can get their own cases"""
        response = requests.get(f"{BASE_URL}/api/cases", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert response.status_code == 200
        cases = response.json()
        assert isinstance(cases, list)
        print("✓ User cases endpoint working")


class TestWarrantyRules:
    """Warranty rules endpoint tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]

    def test_get_warranty_rules(self):
        """Test getting warranty rules (public)"""
        response = requests.get(f"{BASE_URL}/api/warranty-rules")
        assert response.status_code == 200
        rules = response.json()
        assert isinstance(rules, list)
        print(f"✓ Got {len(rules)} warranty rules")

    def test_create_warranty_rule(self, admin_token):
        """Test admin can create warranty rule"""
        response = requests.post(f"{BASE_URL}/api/warranty-rules", 
            json={
                "rule_version": f"test-{uuid.uuid4().hex[:6]}",
                "rule_text": "Test rule for automated testing",
                "keywords": ["test", "automated"]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        rule = response.json()
        assert "id" in rule
        assert rule["rule_text"] == "Test rule for automated testing"
        print("✓ Warranty rule creation working")
        
        # Cleanup - delete the created rule
        requests.delete(f"{BASE_URL}/api/warranty-rules/{rule['id']}", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
