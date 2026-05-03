import pytest
import respx
from httpx import AsyncClient, ASGITransport, Response
from app.auth_server.server import app, stop_event
from unittest.mock import patch

@pytest.mark.asyncio
async def test_auth_twitch():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/auth/twitch")
    assert response.status_code == 307
    assert "id.twitch.tv/oauth2/authorize" in response.headers["location"]

@pytest.mark.asyncio
async def test_shutdown():
    stop_event.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/shutdown")
    assert response.status_code == 200
    assert response.json() == {"message": "Shutting down..."}
    assert stop_event.is_set()

@respx.mock
@pytest.mark.asyncio
@patch("app.auth_server.server.set_token")
async def test_auth_twitch_callback_success(mock_set_token):
    # Mock Twitch token exchange
    respx.post("https://id.twitch.tv/oauth2/token").mock(return_value=Response(
        200, json={"access_token": "test_access", "refresh_token": "test_refresh"}
    ))
    
    # Mock Twitch user info
    respx.get("https://id.twitch.tv/oauth2/userinfo").mock(return_value=Response(
        200, json={"sub": "test_user_id"}
    ))
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/auth/twitch/callback", params={"code": "test_code"})
    
    assert response.status_code == 200
    assert "Authentication Complete!" in response.text
    mock_set_token.assert_called_once_with("test_access", "test_refresh", "test_user_id")

@respx.mock
@pytest.mark.asyncio
async def test_auth_twitch_callback_exchange_error():
    respx.post("https://id.twitch.tv/oauth2/token").mock(return_value=Response(
        400, text="Invalid code"
    ))
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/auth/twitch/callback", params={"code": "bad_code"})
    
    assert response.status_code == 400
    assert "Error exchanging code: Invalid code" in response.text

@pytest.mark.asyncio
async def test_auth_twitch_callback_missing_code():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # FastAPI returns 422 for missing required query parameters
        response = await ac.get("/auth/twitch/callback")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_auth_twitch_callback_empty_code():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/auth/twitch/callback", params={"code": ""})
    # O código no server.py verifica: if not code: return 400
    assert response.status_code == 400
    assert "Error: No code received" in response.text

@respx.mock
@pytest.mark.asyncio
async def test_refresh_token():
    respx.post("https://id.twitch.tv/oauth2/token").mock(return_value=Response(
        200, json={"access_token": "new_access"}
    ))
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/refresh", params={"refresh_token": "old_refresh"})
    
    assert response.status_code == 200
    assert response.json() == {"access_token": "new_access"}
