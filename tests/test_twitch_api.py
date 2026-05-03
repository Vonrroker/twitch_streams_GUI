import pytest
import respx
from httpx import Response
from app.utils.twitch_api import TwitchAPI
from unittest.mock import patch

@pytest.fixture
def mock_env():
    with patch.dict("os.environ", {
        "USER_ID": "test_user",
        "OAUTH_TOKEN": "test_oauth",
        "REFRESH_TOKEN": "test_refresh",
        "TWITCH_SECRET": "test_secret"
    }):
        yield

@respx.mock
@pytest.mark.asyncio
async def test_get_followed_streams_success(mock_env):
    api = TwitchAPI()
    respx.get("https://api.twitch.tv/helix/streams/followed").mock(return_value=Response(
        200, json={"data": [{
            "user_name": "channel1",
            "game_name": "Game 1",
            "viewer_count": 100,
            "title": "Title 1"
        }]}
    ))
    
    streams = await api.get_followed_streams()
    assert len(streams) == 1
    assert streams[0]["channel_name"] == "channel1"

@respx.mock
@pytest.mark.asyncio
@patch("app.utils.twitch_api.set_token")
async def test_get_followed_streams_refresh_retry(mock_set_token, mock_env):
    api = TwitchAPI()
    
    # First call fails with 401
    route = respx.get("https://api.twitch.tv/helix/streams/followed")
    route.side_effect = [
        Response(401),
        Response(200, json={"data": [{"user_name": "channel1", "game_name": "G", "viewer_count": 1, "title": "T"}]})
    ]
    
    # Mock refresh success
    respx.post("https://id.twitch.tv/oauth2/token").mock(return_value=Response(
        200, json={"access_token": "new_oauth", "refresh_token": "new_refresh"}
    ))
    
    streams = await api.get_followed_streams()
    assert len(streams) == 1
    assert api.oauth_token == "new_oauth"
    mock_set_token.assert_called_once()

@respx.mock
@pytest.mark.asyncio
async def test_get_followed_streams_refresh_fail(mock_env):
    api = TwitchAPI()
    respx.get("https://api.twitch.tv/helix/streams/followed").mock(return_value=Response(401))
    respx.post("https://id.twitch.tv/oauth2/token").mock(return_value=Response(400))
    
    streams = await api.get_followed_streams()
    assert streams is None

@pytest.mark.asyncio
async def test_get_followed_streams_no_token():
    with patch.dict("os.environ", {}, clear=True):
        api = TwitchAPI()
        streams = await api.get_followed_streams()
        assert streams is None

@respx.mock
@pytest.mark.asyncio
@patch("app.utils.twitch_api.set_token")
async def test_refresh_access_token_success(mock_set_token, mock_env):
    api = TwitchAPI()
    respx.post("https://id.twitch.tv/oauth2/token").mock(return_value=Response(
        200, json={"access_token": "new_oauth", "refresh_token": "new_refresh"}
    ))
    
    success = await api.refresh_access_token()
    assert success is True
    assert api.oauth_token == "new_oauth"
    mock_set_token.assert_called_with("new_oauth", "new_refresh", "test_user")

@respx.mock
@pytest.mark.asyncio
async def test_refresh_access_token_fail(mock_env):
    api = TwitchAPI()
    respx.post("https://id.twitch.tv/oauth2/token").mock(return_value=Response(400))
    
    success = await api.refresh_access_token()
    assert success is False
