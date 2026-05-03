import asyncio
from unittest.mock import AsyncMock, Mock, patch
import pytest
from textual.widgets import DataTable, Switch
from app.tui import TwitchTUI

@pytest.fixture
def tui_app():
    with patch("app.tui.TwitchAPI") as mock_api:
        app = TwitchTUI()
        app.api = mock_api.return_value
        return app

@pytest.mark.asyncio
async def test_refresh_streams_no_streams(tui_app):
    """Test refresh_streams with no streams returned."""
    # We need to mock the TwitchAPI constructor because it's called inside refresh_streams
    with patch("app.tui.TwitchAPI") as MockAPI:
        mock_api_instance = MockAPI.return_value
        mock_api_instance.oauth_token = "token"
        mock_api_instance.get_followed_streams = AsyncMock(return_value=[])
        
        mock_table = Mock(spec=DataTable)
        with patch.object(tui_app, "query_one", return_value=mock_table), \
             patch.object(tui_app, "notify") as mock_notify, \
             patch("app.tui.load_dotenv"):
            await tui_app.refresh_streams()
            mock_notify.assert_called_with("No live streams found or error fetching.", severity="error")

@pytest.mark.asyncio
async def test_refresh_streams_exception(tui_app):
    """Test refresh_streams with an exception."""
    with patch("app.tui.TwitchAPI") as MockAPI:
        mock_api_instance = MockAPI.return_value
        mock_api_instance.oauth_token = "token"
        mock_api_instance.get_followed_streams = AsyncMock(side_effect=Exception("API Error"))
        
        mock_table = Mock(spec=DataTable)
        with patch.object(tui_app, "query_one", return_value=mock_table), \
             patch.object(tui_app, "notify") as mock_notify, \
             patch("app.tui.load_dotenv"):
            await tui_app.refresh_streams()
            mock_notify.assert_called()
            assert "API Error" in mock_notify.call_args[0][0]

@pytest.mark.asyncio
async def test_action_toggle_best(tui_app):
    """Test action_toggle_best."""
    mock_switch = Mock(spec=Switch)
    mock_switch.value = True
    with patch.object(tui_app, "query_one", return_value=mock_switch), \
         patch.object(tui_app, "notify") as mock_notify:
        await tui_app.action_toggle_best()
        assert mock_switch.value is False
        mock_notify.assert_called_with("Auto-Best: Disabled")

@pytest.mark.asyncio
async def test_handle_row_selection_exception(tui_app):
    """Test handle_row_selection with an exception."""
    mock_table = Mock(spec=DataTable)
    mock_table.get_row.side_effect = Exception("Table Error")
    with patch.object(tui_app, "query_one", return_value=mock_table), \
         patch.object(tui_app, "notify") as mock_notify:
        await tui_app.handle_row_selection("key")
        mock_notify.assert_called()
        assert "Table Error" in mock_notify.call_args[0][0]

@pytest.mark.asyncio
async def test_play_stream_no_resolutions(tui_app):
    """Test play_stream when no resolutions are found."""
    mock_switch = Mock(spec=Switch)
    mock_switch.value = False
    with patch.object(tui_app, "query_one", return_value=mock_switch), \
         patch("streamlink.Streamlink") as mock_sl_class, \
         patch("app.tui.asyncio.to_thread") as mock_to_thread, \
         patch.object(tui_app, "notify") as mock_notify, \
         patch.object(tui_app, "run_streamlink") as mock_run:
        
        mock_to_thread.return_value = {"best": Mock(), "worst": Mock()}
        await tui_app.play_stream("channel")
        mock_run.assert_called_with("channel", "best")
        mock_notify.assert_any_call("No resolutions found, playing 'best'.", severity="warning")

@pytest.mark.asyncio
async def test_play_stream_exception(tui_app):
    """Test play_stream with an exception."""
    mock_switch = Mock(spec=Switch)
    mock_switch.value = False
    with patch.object(tui_app, "query_one", return_value=mock_switch), \
         patch("app.tui.asyncio.to_thread", side_effect=Exception("Streamlink Error")), \
         patch.object(tui_app, "notify") as mock_notify:
        await tui_app.play_stream("channel")
        mock_notify.assert_any_call("Error: Streamlink Error", severity="error")
