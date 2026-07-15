import pytest


@pytest.fixture
def normal_auth_client(client, auth_client):
    auth_client.post(
        "/api/admin/users", json={"username": "profuser", "password": "profpassword"}
    )
    r = client.post(
        "/api/login", json={"username": "profuser", "password": "profpassword"}
    )
    token = r.json().get("token")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_update_profile_valid_social_links(normal_auth_client):
    normal_auth_client.post("/api/profiles", json={"username": "myprofile"})

    # Needs X-Active-Profile to update me
    normal_auth_client.headers.update({"X-Active-Profile": "myprofile"})

    r = normal_auth_client.put(
        "/api/me",
        json={
            "username": "myprofile",
            "social_links": [
                {"platform": "twitter", "url": "https://twitter.com/test"},
                {
                    "platform": "github",
                    "url": "https://github.com/test",
                    "title": "My Code",
                },
            ],
        },
    )

    assert r.status_code == 200
    assert len(r.json()["social_links"]) == 2
    assert r.json()["social_links"][0]["platform"] == "twitter"


def test_update_profile_invalid_social_links(normal_auth_client):
    normal_auth_client.post("/api/profiles", json={"username": "badprofile"})
    normal_auth_client.headers.update({"X-Active-Profile": "badprofile"})

    r = normal_auth_client.put(
        "/api/me",
        json={
            "username": "badprofile",
            "social_links": [
                {
                    "platform": "<script>alert(1)</script>",
                    "url": "https://twitter.com/test",
                }
            ],
        },
    )

    # Should be rejected by pydantic regex validation
    assert r.status_code == 422


def test_account_can_create_up_to_five_profiles(normal_auth_client):
    for number in range(1, 6):
        response = normal_auth_client.post(
            "/api/profiles", json={"username": f"profile-{number}"}
        )
        assert response.status_code == 200

    profiles_response = normal_auth_client.get("/api/profiles")
    assert profiles_response.status_code == 200
    assert len(profiles_response.json()["profiles"]) == 5
    assert profiles_response.json()["max_profiles"] == 5

    sixth_response = normal_auth_client.post(
        "/api/profiles", json={"username": "profile-6"}
    )
    assert sixth_response.status_code == 400
    assert sixth_response.json()["error"]["message"] == (
        "Maximum of 5 profiles allowed per account"
    )
