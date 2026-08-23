import pytest
from httpx import AsyncClient

from app.modules.identity.internal.auth_provider import (
    FirebaseAuthProvider,
    get_auth_provider,
)


@pytest.mark.asyncio
async def test_register_creates_tenant_and_owner(client: AsyncClient) -> None:
    payload = {
        "org_name": "Acme University",
        "name": "Prof. Alice",
        "email": "alice@acme.edu",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["user"]["name"] == "Prof. Alice"
    assert data["user"]["email"] == "alice@acme.edu"
    assert data["user"]["role"] == "owner"
    assert data["tenant"]["name"] == "Acme University"
    assert data["tenant"]["slug"] == "acme-university"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_login_and_wrong_password(client: AsyncClient) -> None:
    # 1. Register user
    reg_payload = {
        "org_name": "Beta Labs",
        "name": "Bob Stone",
        "email": "bob@betalabs.com",
        "password": "Password12345!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201

    # 2. Login with correct password
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@betalabs.com", "password": "Password12345!"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["email"] == "bob@betalabs.com"
    assert "access_token" in login_res.json()["tokens"]

    # 3. Login with wrong password -> 401
    wrong_pwd_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@betalabs.com", "password": "WrongPassword!"},
    )
    assert wrong_pwd_res.status_code == 401
    assert "Invalid email or password" in wrong_pwd_res.json()["detail"]

    # 4. Login with non-existent email -> 401
    non_existent_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@nowhere.com", "password": "Password12345!"},
    )
    assert non_existent_res.status_code == 401


@pytest.mark.asyncio
async def test_guest_flow_creates_sandbox(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/guest")
    assert response.status_code == 201
    data = response.json()

    assert data["user"]["role"] == "student"
    assert data["user"]["name"] == "Guest Learner"
    assert data["tenant"]["slug"].startswith("demo-guest-")
    assert data["tenant"]["name"] == "Demo Sandbox"
    assert "access_token" in data["tokens"]


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient) -> None:
    # 1. Create a guest session to get tokens
    guest_res = await client.post("/api/v1/auth/guest")
    assert guest_res.status_code == 201
    refresh_token = guest_res.json()["tokens"]["refresh_token"]

    # 2. Refresh token
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # 3. Invalid refresh token -> 401
    invalid_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.jwt.token"},
    )
    assert invalid_res.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint_and_unauthorized(client: AsyncClient) -> None:
    # 1. Register user
    reg_payload = {
        "org_name": "Gamma AI",
        "name": "Gamma Admin",
        "email": "admin@gamma.ai",
        "password": "PasswordGamma123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["tokens"]["access_token"]

    # 2. Call /me with Bearer token
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["user"]["email"] == "admin@gamma.ai"
    assert data["tenant"]["name"] == "Gamma AI"

    # 3. Call /me without token -> 401 / 403
    unauth_res = await client.get("/api/v1/auth/me")
    assert unauth_res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_firebase_provider_stub_raises() -> None:
    provider = get_auth_provider("firebase")
    assert isinstance(provider, FirebaseAuthProvider)

    with pytest.raises(NotImplementedError):
        provider.hash_password("any_password")

    with pytest.raises(NotImplementedError):
        provider.verify_password("any_password", "hash")
