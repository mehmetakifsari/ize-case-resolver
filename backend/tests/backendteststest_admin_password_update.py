from fastapi import FastAPI
from fastapi.testclient import TestClient

import routes.admin as admin_routes
import routes.auth as auth_routes
from services.auth import get_password_hash


class FakeUpdateResult:
    def __init__(self, matched_count: int):
        self.matched_count = matched_count


class FakeUsersCollection:
    def __init__(self, users):
        self.users_by_id = {user["id"]: user for user in users}

    async def find_one(self, query, projection=None):
        if "id" in query:
            user = self.users_by_id.get(query["id"])
        elif "email" in query:
            user = next((u for u in self.users_by_id.values() if u["email"] == query["email"]), None)
        else:
            user = None

        if not user:
            return None

        if projection and projection.get("hashed_password") == 0:
            return {k: v for k, v in user.items() if k != "hashed_password"}

        return dict(user)

    async def update_one(self, query, update):
        user = self.users_by_id.get(query.get("id"))
        if not user:
            return FakeUpdateResult(0)

        for key, value in update.get("$set", {}).items():
            user[key] = value
        return FakeUpdateResult(1)


class FakeDB:
    def __init__(self, users):
        self.users = FakeUsersCollection(users)


ADMIN_USER = {
    "id": "admin-1",
    "email": "admin@example.com",
    "full_name": "Admin User",
    "role": "admin",
    "is_active": True,
    "hashed_password": get_password_hash("Admin123!"),
}

NORMAL_USER = {
    "id": "user-1",
    "email": "user@example.com",
    "full_name": "Normal User",
    "role": "user",
    "is_active": True,
    "hashed_password": get_password_hash("OldPass123!"),
}


def build_client():
    fake_db = FakeDB([ADMIN_USER.copy(), NORMAL_USER.copy()])
    admin_routes.db = fake_db
    auth_routes.db = fake_db

    app = FastAPI()
    app.include_router(admin_routes.router, prefix="/api")
    app.include_router(auth_routes.router, prefix="/api")
    app.dependency_overrides[admin_routes.get_admin_user] = lambda: ADMIN_USER

    return TestClient(app)


def test_update_user_password_success():
    client = build_client()

    response = client.patch(
        "/api/admin/users/user-1/password",
        json={"new_password": "NewPass123!"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Şifre güncellendi"}


def test_update_user_password_weak_password_validation():
    client = build_client()

    response = client.patch(
        "/api/admin/users/user-1/password",
        json={"new_password": "weak"},
    )

    assert response.status_code == 422


def test_update_user_password_user_not_found():
    client = build_client()

    response = client.patch(
        "/api/admin/users/missing-user/password",
        json={"new_password": "StrongPass123!"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Kullanıcı bulunamadı"


def test_login_works_with_updated_password():
    client = build_client()

    patch_response = client.patch(
        "/api/admin/users/user-1/password",
        json={"new_password": "BrandNew123!"},
    )
    assert patch_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "BrandNew123!"},
    )

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["id"] == "user-1"