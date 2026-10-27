"""Pytest tests for Lab 5's SQLite user functions and Flask user API.

Run from the same directory as app.py:
    python -m pytest -v test_user_Kevin_Antoun.py

The tests use a separate temporary SQLite database for every test. They never
read from or modify the repository's real database.db file.
"""

import sqlite3

import pytest

import app as lab_app


USER_1 = {
    "name": "Alice Test",
    "email": "alice@example.com",
    "phone": "70123456",
    "address": "Beirut",
    "country": "Lebanon",
}

USER_2 = {
    "name": "Bob Test",
    "email": "bob@example.com",
    "phone": "76123456",
    "address": "Tripoli",
    "country": "Lebanon",
}

UPDATED_USER = {
    "name": "Alice Updated",
    "email": "alice.updated@example.com",
    "phone": "71111111",
    "address": "Jounieh",
    "country": "Lebanon",
}

# The current Lab 5 app.py creates the users table but does NOT seed user rows.
# If your assignment specifies initial users, add those user dictionaries here
# and implement the matching automatic insertion in app.py. Test 1 will then
# verify that the required users really are created at initialization.
EXPECTED_INITIAL_USERS = []


def assert_user_matches(actual, expected):
    """Check all uploaded/downloaded user fields, allowing an assigned ID."""
    assert isinstance(actual, dict)
    assert isinstance(actual.get("user_id"), int)
    assert actual["user_id"] > 0
    for field in ("name", "email", "phone", "address", "country"):
        assert actual[field] == expected[field], f"Incorrect {field}"


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Redirect the original app's database connections to a temporary file."""
    db_path = tmp_path / "database.db"
    monkeypatch.setattr(
        lab_app,
        "connect_to_db",
        lambda: sqlite3.connect(str(db_path)),
    )
    return db_path


@pytest.fixture
def initialized_database(isolated_database):
    lab_app.create_db_table()
    return isolated_database


@pytest.fixture
def client(initialized_database):
    lab_app.app.config.update(TESTING=True)
    with lab_app.app.test_client() as test_client:
        yield test_client


def test_01_database_created_with_initial_users(isolated_database):
    """1. First-run database/table creation and expected initial records."""
    assert not isolated_database.exists()

    lab_app.create_db_table()

    assert isolated_database.is_file()
    with sqlite3.connect(isolated_database) as conn:
        fields = [row[1] for row in conn.execute("PRAGMA table_info(users)")]

    assert fields == [
        "user_id", "name", "email", "phone", "address", "country"
    ]
    assert lab_app.get_users() == EXPECTED_INITIAL_USERS


def test_02_insert_user(initialized_database):
    """2. insert_user() returns and persists all inserted fields."""
    inserted = lab_app.insert_user(USER_1.copy())

    assert_user_matches(inserted, USER_1)
    assert lab_app.get_user_by_id(inserted["user_id"]) == inserted


def test_03_get_users(initialized_database):
    """3. get_users() returns the inserted users and their information."""
    first = lab_app.insert_user(USER_1.copy())
    second = lab_app.insert_user(USER_2.copy())

    users = lab_app.get_users()

    assert len(users) == 2
    assert sorted(users, key=lambda user: user["user_id"]) == [first, second]


def test_04_get_user_by_id(initialized_database):
    """4. get_user_by_id() returns only the requested user."""
    first = lab_app.insert_user(USER_1.copy())
    lab_app.insert_user(USER_2.copy())

    found = lab_app.get_user_by_id(first["user_id"])

    assert found == first
    assert lab_app.get_user_by_id(-1) == {}


def test_05_update_user(initialized_database):
    """5. update_user() returns updated fields and saves them to SQLite."""
    original = lab_app.insert_user(USER_1.copy())
    payload = {**UPDATED_USER, "user_id": original["user_id"]}

    updated = lab_app.update_user(payload)

    assert_user_matches(updated, UPDATED_USER)
    assert updated["user_id"] == original["user_id"]
    assert lab_app.get_user_by_id(original["user_id"]) == payload


def test_06_delete_user(initialized_database):
    """6. delete_user() deletes the selected record."""
    inserted = lab_app.insert_user(USER_1.copy())

    result = lab_app.delete_user(inserted["user_id"])

    assert result == {"status": "User deleted successfully"}
    assert lab_app.get_user_by_id(inserted["user_id"]) == {}
    assert lab_app.get_users() == []


def test_07_api_get_user(client):
    """7. GET /api/users/<id>: HTTP status and downloaded JSON."""
    inserted = lab_app.insert_user(USER_1.copy())

    response = client.get(f"/api/users/{inserted['user_id']}")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == inserted


def test_08_api_add_user(client):
    """8. POST /api/users/add: HTTP status, uploaded data, returned data."""
    response = client.post("/api/users/add", json=USER_1)

    assert response.status_code == 200
    assert response.is_json
    created = response.get_json()
    assert_user_matches(created, USER_1)
    assert lab_app.get_user_by_id(created["user_id"]) == created


def test_09_api_update_user(client):
    """9. PUT /api/users/update: HTTP status and updated JSON/record."""
    inserted = lab_app.insert_user(USER_1.copy())
    payload = {**UPDATED_USER, "user_id": inserted["user_id"]}

    response = client.put("/api/users/update", json=payload)

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == payload
    assert lab_app.get_user_by_id(inserted["user_id"]) == payload


def test_10_api_delete_user(client):
    """10. DELETE /api/users/delete/<id>: HTTP status, JSON, and deletion."""
    inserted = lab_app.insert_user(USER_1.copy())

    response = client.delete(f"/api/users/delete/{inserted['user_id']}")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"status": "User deleted successfully"}
    assert lab_app.get_user_by_id(inserted["user_id"]) == {}
