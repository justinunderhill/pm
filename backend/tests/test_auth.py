from fastapi.testclient import TestClient


def test_session_endpoint_unauthenticated(client: TestClient) -> None:
    response = client.get("/api/auth/session")

    assert response.status_code == 200
    assert response.json() == {"authenticated": False, "username": None}


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."


def test_login_sets_session_cookie_and_allows_protected_route(client: TestClient) -> None:
    login = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert login.status_code == 200
    assert "pm_session" in login.cookies

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json() == {"username": "user"}

    session = client.get("/api/auth/session")
    assert session.status_code == 200
    assert session.json() == {"authenticated": True, "username": "user"}


def test_logout_clears_session(client: TestClient) -> None:
    client.post("/api/auth/login", json={"username": "user", "password": "password"})

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert logout.json() == {"ok": True}

    me = client.get("/api/auth/me")
    assert me.status_code == 401
    assert me.json()["detail"] == "Authentication required."


def test_protected_route_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."
