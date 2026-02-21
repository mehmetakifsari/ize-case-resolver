from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

import routes.admin as admin_routes


class FakeUsersCollection:
    def __init__(self):
        self.users = {}

    async def find_one(self, query, projection=None):
        if "email" in query:
            return self.users.get(query["email"])
        return None

    async def insert_one(self, doc):
        if doc["email"] in self.users:
            raise DuplicateKeyError("E11000 duplicate key error collection: users index: email_1 dup key")
        self.users[doc["email"]] = dict(doc)


class FakeDB:
    def __init__(self):
        self.users = FakeUsersCollection()


ADMIN_USER = {
    "id": "admin-1",
    "role": "admin",
    "is_active": True,
}


def build_client():
    fake_db = FakeDB()
    admin_routes.db = fake_db

    app = FastAPI()
    app.include_router(admin_routes.router, prefix="/api")
    app.dependency_overrides[admin_routes.get_admin_user] = lambda: ADMIN_USER

    return TestClient(app), fake_db


def test_create_user_normalizes_email_to_lowercase():
    client, fake_db = build_client()

    response = client.post(
        "/api/admin/users",
        json={
            "email": "MixedCase@Example.com",
            "password": "StrongPass123!",
            "full_name": "Demo User",
            "phone_number": "",
            "branch": "",
            "role": "user",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "mixedcase@example.com"
    assert "mixedcase@example.com" in fake_db.users.users


def test_create_user_returns_400_when_duplicate_email_insert_race_happens():
    client, fake_db = build_client()
    fake_db.users.users["existing@example.com"] = {
        "id": "existing",
        "email": "existing@example.com",
    }

    response = client.post(
        "/api/admin/users",
        json={
            "email": "existing@example.com",
            "password": "StrongPass123!",
            "full_name": "Demo User",
            "phone_number": "",
            "branch": "",
            "role": "user",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Bu email adresi zaten kayıtlı"