import pytest
from fastapi.testclient import TestClient

from src import app as api


@pytest.fixture
def client(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Practice chess",
            "schedule": "Fridays, 3:30 PM",
            "max_participants": 12,
            "participants": ["Existing@mergington.edu"],
        }
    }
    monkeypatch.setattr(api, "activities", activities)
    return TestClient(api.app)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected = {
        "Chess Club": {
            "description": "Practice chess",
            "schedule": "Fridays, 3:30 PM",
            "max_participants": 12,
            "participants": ["Existing@mergington.edu"],
        }
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_normalizes_email_and_adds_participant(client):
    # Arrange
    email = "  NEW@MergingTon.edu  "

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@mergington.edu for Chess Club"
    }
    assert api.activities["Chess Club"]["participants"] == [
        "Existing@mergington.edu",
        "new@mergington.edu",
    ]


def test_signup_rejects_duplicate_email_case_insensitively(client):
    # Arrange
    email = " EXISTING@MERGINGTON.EDU "

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert api.activities["Chess Club"]["participants"] == [
        "Existing@mergington.edu"
    ]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422
    assert api.activities[activity_name]["participants"] == [
        "Existing@mergington.edu"
    ]


def test_unregister_removes_matching_participant(client):
    # Arrange
    email = " EXISTING@MERGINGTON.EDU "

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered Existing@mergington.edu from Chess Club"
    }
    assert api.activities["Chess Club"]["participants"] == []


def test_unregister_returns_not_found_for_unregistered_student(client):
    # Arrange
    email = "missing@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert api.activities["Chess Club"]["participants"] == [
        "Existing@mergington.edu"
    ]