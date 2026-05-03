import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from textual.widgets import Switch, DataTable

from app.tui import ResolutionSelect, TwitchTUI


class TestResolutionSelect:
    """Test suite for ResolutionSelect modal screen."""

    def test_resolution_select_initialization(self):
        """Test ResolutionSelect initializes with resolutions and channel."""
        resolutions = ["720p", "1080p", "480p"]
        channel = "testchannel"

        screen = ResolutionSelect(resolutions, channel)

        assert screen.resolutions == resolutions
        assert screen.channel == channel

    def test_resolution_select_on_button_pressed(self):
        """Test ResolutionSelect dismisses with selected resolution."""
        screen = ResolutionSelect(["720p", "1080p"], "testchannel")

        mock_button = Mock()
        mock_button.label = "1080p"
        mock_event = Mock()
        mock_event.button = mock_button

        with patch.object(screen, "dismiss") as mock_dismiss:
            screen.on_button_pressed(mock_event)
            mock_dismiss.assert_called_once_with("1080p")

    def test_resolution_select_on_key_escape(self):
        """Test ResolutionSelect dismisses on escape key."""
        screen = ResolutionSelect(["720p"], "testchannel")

        mock_event = Mock()
        mock_event.key = "escape"

        with patch.object(screen, "dismiss") as mock_dismiss:
            screen.on_key(mock_event)
            mock_dismiss.assert_called_once_with(None)

    def test_resolution_select_on_key_navigation(self):
        """Test ResolutionSelect handles arrow key navigation."""
        screen = ResolutionSelect(["720p", "1080p"], "testchannel")

        with patch.object(screen, "focus_next") as mock_next, \
             patch.object(screen, "focus_previous") as mock_prev:

            # Test down arrow
            mock_event = Mock()
            mock_event.key = "down"
            screen.on_key(mock_event)
            mock_next.assert_called_once()

            # Test up arrow
            mock_event = Mock()
            mock_event.key = "up"
            screen.on_key(mock_event)
            mock_prev.assert_called_once()

    def test_resolution_select_focus_first_button(self):
        """Test focus_first_button focuses the first button."""
        screen = ResolutionSelect(["720p", "1080p"], "testchannel")
        mock_button = Mock()
        mock_buttons = Mock()
        mock_buttons.first.return_value = mock_button
        
        with patch.object(screen, "query", return_value=mock_buttons):
            screen.focus_first_button()
            mock_buttons.first.assert_called_once()
            mock_button.focus.assert_called_once()

    def test_resolution_select_on_mount(self):
        """Test on_mount calls call_after_refresh with focus_first_button."""
        screen = ResolutionSelect(["720p"], "testchannel")
        with patch.object(screen, "call_after_refresh") as mock_call:
            screen.on_mount()
            mock_call.assert_called_once_with(screen.focus_first_button)


class TestTwitchTUI:
    """Test suite for TwitchTUI app."""

    @pytest.fixture
    def tui_app(self):
        """Create a TwitchTUI instance for testing."""
        with patch("app.tui.TwitchAPI") as mock_api:
            app = TwitchTUI()
            app.api = mock_api.return_value
            return app

    def test_tui_initialization(self, tui_app):
        """Test TwitchTUI initializes correctly."""
        assert tui_app.TITLE == "Twitch Streams TUI"
        assert tui_app.api is not None
        assert tui_app.BINDINGS is not None

    def test_tui_bindings(self, tui_app):
        """Test TwitchTUI has required bindings."""
        binding_keys = [binding.key for binding in tui_app.BINDINGS]
        assert "q" in binding_keys
        assert "r" in binding_keys
        assert "b" in binding_keys

    @pytest.mark.asyncio
    async def test_authenticate_success(self, tui_app):
        """Test authentication succeeds and token is saved."""
        with patch("app.tui.run_server"), \
             patch("app.tui.webbrowser.open") as mock_browser, \
             patch("app.tui.load_dotenv"), \
             patch.dict("os.environ", {"OAUTH_TOKEN": "test_token"}), \
             patch.object(tui_app, "notify") as mock_notify, \
             patch.object(tui_app, "refresh_streams", new_callable=AsyncMock) as mock_refresh:

            await tui_app.authenticate()

            mock_browser.assert_called_once_with("http://localhost:5000/auth/twitch")
            mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_timeout(self, tui_app):
        """Test authentication times out."""
        with patch("app.tui.run_server"), \
             patch("app.tui.webbrowser.open"), \
             patch("app.tui.load_dotenv"), \
             patch.dict("os.environ", {}, clear=True), \
             patch.object(tui_app, "notify") as mock_notify:

            # Mock asyncio.sleep to return instantly, allowing authenticate's own timeout logic to trigger quickly.
            # This ensures the test doesn't wait for the full timeout duration.
            mock_sleep = AsyncMock()
            mock_sleep.return_value = None # Make await asyncio.sleep() return None instantly.
            
            with patch("asyncio.sleep", mock_sleep):
                # Let authenticate run its course. If no token is found and the internal timeout triggers,
                # it should call notify.
                await tui_app.authenticate()

            # Check for timeout notification
            timeout_calls = [
                call for call in mock_notify.call_args_list
                if "timed out" in call[0][0].lower()
            ]
            assert len(timeout_calls) > 0, "Notification for timeout was not found."

    @pytest.mark.asyncio
    async def test_refresh_streams_no_streams_found(self, tui_app):
        """Test refresh_streams when no live streams are found."""
        # Patch TwitchAPI class so that instances created within refresh_streams are controlled
        with patch("app.tui.TwitchAPI") as MockTwitchAPI, \
             patch.dict("os.environ", {"OAUTH_TOKEN": "dummy_token"}): # Ensure token is present

            # Configure the mock instance that TwitchAPI() will return
            mock_api_instance = MockTwitchAPI.return_value
            mock_api_instance.oauth_token = "dummy_token" # Ensure token is present on the instance
            mock_api_instance.get_followed_streams = AsyncMock(return_value=[])

            # Mock query_one to avoid ScreenStackError during direct method call
            mock_datatable = Mock()
            mock_datatable.clear = Mock() # Mock the clear method too
            with patch.object(tui_app, "query_one", return_value=mock_datatable) as mock_query_one, \
                 patch.object(tui_app, "notify") as mock_notify:

                await tui_app.refresh_streams()
                
                mock_query_one.assert_called_once_with(DataTable)
                mock_datatable.clear.assert_called_once()
                mock_notify.assert_called_once_with("No live streams found or error fetching.", severity="error")

    @pytest.mark.asyncio
    async def test_refresh_streams_api_error(self, tui_app):
        """Test refresh_streams when TwitchAPI raises an error."""
        # Patch TwitchAPI class and os.environ
        with patch("app.tui.TwitchAPI") as MockTwitchAPI, \
             patch.dict("os.environ", {"OAUTH_TOKEN": "dummy_token"}):

            mock_api_instance = MockTwitchAPI.return_value
            mock_api_instance.oauth_token = "dummy_token"
            mock_api_instance.get_followed_streams = AsyncMock(side_effect=Exception("API Error"))

            # Mock query_one to avoid ScreenStackError during direct method call
            mock_datatable = Mock()
            mock_datatable.clear = Mock()
            with patch.object(tui_app, "query_one", return_value=mock_datatable) as mock_query_one, \
                 patch.object(tui_app, "notify") as mock_notify:

                await tui_app.refresh_streams()

                mock_query_one.assert_called_once_with(DataTable)
                mock_datatable.clear.assert_called_once()
                # Assert that the notification includes the error message
                mock_notify.assert_called_once() # Check it was called once
                # Check the content of the notification
                args, kwargs = mock_notify.call_args
                assert "Error fetching streams:" in args[0]
                assert kwargs.get("severity") == "error"
    @pytest.mark.asyncio
    async def test_action_refresh(self, tui_app):
        """Test refresh action calls refresh_streams."""
        with patch.object(tui_app, "refresh_streams", new_callable=AsyncMock) as mock_refresh:
            await tui_app.action_refresh()
            mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_toggle_best_enables(self, tui_app):
        """Test toggle auto-best resolution action when disabled."""
        mock_switch = Mock(spec=Switch)
        mock_switch.value = False

        with patch.object(tui_app, "query_one", return_value=mock_switch), \
             patch.object(tui_app, "notify") as mock_notify:

            await tui_app.action_toggle_best()

            assert mock_switch.value is True
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args[0][0]
            assert "Enabled" in call_args

    @pytest.mark.asyncio
    async def test_action_toggle_best_disables(self, tui_app):
        """Test toggle auto-best resolution action when enabled."""
        mock_switch = Mock(spec=Switch)
        mock_switch.value = True

        with patch.object(tui_app, "query_one", return_value=mock_switch), \
             patch.object(tui_app, "notify") as mock_notify:

            await tui_app.action_toggle_best()

            assert mock_switch.value is False
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args[0][0]
            assert "Disabled" in call_args

    @pytest.mark.asyncio
    async def test_handle_row_selection_valid(self, tui_app):
        """Test handle_row_selection with valid row."""
        mock_table = Mock()
        mock_table.get_row.return_value = ("testchannel", "1000", "Game", "Title")

        with patch.object(tui_app, "query_one", return_value=mock_table), \
             patch.object(tui_app, "play_stream", new_callable=AsyncMock) as mock_play:

            await tui_app.handle_row_selection("testchannel")

            mock_play.assert_called_once_with("testchannel")

    @pytest.mark.asyncio
    async def test_handle_row_selection_error(self, tui_app):
        """Test handle_row_selection with error."""
        mock_table = Mock()
        mock_table.get_row.side_effect = Exception("Row not found")

        with patch.object(tui_app, "query_one", return_value=mock_table), \
             patch.object(tui_app, "notify") as mock_notify:

            await tui_app.handle_row_selection("invalid_key")

            mock_notify.assert_called_once()
            call_args = mock_notify.call_args[0][0]
            assert "Error selecting row" in call_args

    @pytest.mark.asyncio
    async def test_play_stream_auto_best(self, tui_app):
        """Test play_stream with auto-best resolution."""
        mock_switch = Mock(spec=Switch)
        mock_switch.value = True

        with patch.object(tui_app, "query_one", return_value=mock_switch), \
             patch.object(tui_app, "run_streamlink") as mock_streamlink:

            await tui_app.play_stream("testchannel")

            mock_streamlink.assert_called_once_with("testchannel", "best")

    @pytest.mark.asyncio
    async def test_play_stream_manual_resolution(self, tui_app):
        """Test play_stream with manual resolution selection."""
        mock_switch = Mock(spec=Switch)
        mock_switch.value = False

        # Mock streamlink session and streams
        mock_streams = {"720p": Mock(), "1080p": Mock(), "best": Mock(), "worst": Mock()}
        
        with patch.object(tui_app, "query_one", return_value=mock_switch), \
             patch("app.tui.asyncio.to_thread", new_callable=AsyncMock, return_value=mock_streams), \
             patch("app.tui.ResolutionSelect") as MockResSelect, \
             patch.object(tui_app, "push_screen") as mock_push:

            await tui_app.play_stream("testchannel")

            mock_push.assert_called_once()
            args = mock_push.call_args[0]
            assert isinstance(args[0], MockResSelect.return_value.__class__)
            # The second arg is the callback
            assert callable(args[1])

    @pytest.mark.asyncio
    async def test_play_stream_no_resolutions(self, tui_app):
        """Test play_stream when no resolutions are found."""
        mock_switch = Mock(spec=Switch)
        mock_switch.value = False

        # Mock streamlink session with only best/worst
        mock_streams = {"best": Mock(), "worst": Mock()}
        
        with patch.object(tui_app, "query_one", return_value=mock_switch), \
             patch("app.tui.asyncio.to_thread", new_callable=AsyncMock, return_value=mock_streams), \
             patch.object(tui_app, "run_streamlink") as mock_run, \
             patch.object(tui_app, "notify") as mock_notify:

            await tui_app.play_stream("testchannel")

            mock_run.assert_called_once_with("testchannel", "best")
            assert mock_notify.call_count == 2
            assert "No resolutions found" in mock_notify.call_args_list[1][0][0]

    @pytest.mark.asyncio
    async def test_play_stream_error(self, tui_app):
        """Test play_stream when streamlink raises an error."""
        mock_switch = Mock(spec=Switch)
        mock_switch.value = False

        with patch.object(tui_app, "query_one", return_value=mock_switch), \
             patch("app.tui.asyncio.to_thread", new_callable=AsyncMock, side_effect=Exception("Streamlink Error")), \
             patch.object(tui_app, "notify") as mock_notify:

            await tui_app.play_stream("testchannel")

            assert mock_notify.call_count == 2
            assert "Error: Streamlink Error" in mock_notify.call_args_list[1][0][0]

    def test_run_streamlink(self, tui_app):
        """Test run_streamlink launches subprocess."""
        with patch("app.tui.subprocess.Popen") as mock_popen, \
             patch.object(tui_app, "notify") as mock_notify:

            tui_app.run_streamlink("testchannel", "720p")

            mock_popen.assert_called_once()
            cmd = mock_popen.call_args[0][0]
            assert "streamlink" in cmd
            assert "testchannel" in cmd
            assert "720p" in cmd
            mock_notify.assert_called_once()
            assert "Launching" in mock_notify.call_args[0][0]

    def test_run_streamlink_uses_devnull(self, tui_app):
        """Test run_streamlink redirects output to DEVNULL."""
        with patch("app.tui.subprocess.Popen") as mock_popen, \
             patch("app.tui.subprocess.DEVNULL", 3):

            tui_app.run_streamlink("testchannel", "720p")

            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs["stdout"] == 3
            assert call_kwargs["stderr"] == 3
            assert call_kwargs["shell"] is True
