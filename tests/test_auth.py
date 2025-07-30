import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.api import app


def test_login_success():
    """Test successful login."""
    with TestClient(app) as client:
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["token"]["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"


def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    with TestClient(app) as client:
        response = client.post("/auth/login", json={
            "username": "wronguser",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password"


def test_logout():
    """Test logout functionality."""
    with TestClient(app) as client:
        # First login to get a token
        login_response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]["access_token"]
        
        # Then logout
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            json={"session_id": login_response.json()["session_id"]}
        )
        assert logout_response.status_code == 204
