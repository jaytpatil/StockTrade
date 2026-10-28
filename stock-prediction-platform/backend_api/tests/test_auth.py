import pytest

def test_register_user_success(client):
    response = client.post("/auth/register", json={
        "email": "new_user@example.com",
        "password": "securepassword123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new_user@example.com"
    assert "id" in data
    assert data["role"] == "user"

def test_register_user_duplicate_email(client):
    # Intentional duplicate attempt leveraging the user created above
    response = client.post("/auth/register", json={
        "email": "new_user@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_success(client):
    response = client.post("/auth/login", data={
        "username": "new_user@example.com",
        "password": "securepassword123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    response = client.post("/auth/login", data={
        "username": "new_user@example.com",
        "password": "WRONG_PASSWORD"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"
