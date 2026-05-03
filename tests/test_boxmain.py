import pytest
from unittest.mock import Mock, patch, MagicMock
from kivy.app import App as KivyApp
from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest

from app.boxmain import BoxMain
from tests.fakes.list_streams import fake_list_streams


class DummyMDApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls = ThemeManager()


@pytest.fixture(autouse=True)
def md_app():
    previous_app = KivyApp._running_app
    app = DummyMDApp()
    KivyApp._running_app = app
    yield app
    KivyApp._running_app = previous_app


@pytest.fixture
def mock_grid_streams():
    """Mock grid_streams widget"""
    mock_grid = Mock()
    mock_grid.cols = 3
    mock_grid.children = []
    mock_grid.clear_widgets = Mock()
    mock_grid.add_widget = Mock()
    return mock_grid


@pytest.fixture
def mock_scrollview():
    """Mock scrollview widget"""
    mock_scroll = Mock()
    mock_scroll.vbar = [0.5, 0.3]  # [position, size]
    mock_scroll.scroll_y = 0.5
    return mock_scroll


@pytest.fixture
def mock_popup():
    """Mock popup widget"""
    mock_popup = Mock()
    mock_popup.open = Mock()
    mock_popup.dismiss = Mock()
    mock_popup.chk_vlc = False
    return mock_popup


@pytest.fixture
def mock_popup_auth():
    """Mock PopUpAuth widget"""
    mock_popup = Mock()
    mock_popup.open = Mock()
    mock_popup.dismiss = Mock()
    mock_popup.ids = {
        "content_container": Mock(children=[Mock(children=[Mock(ids={"token": Mock(text="token.refresh.user")})])])
    }
    return mock_popup
    """Mock popup widget"""
    mock_popup = Mock()
    mock_popup.open = Mock()
    mock_popup.dismiss = Mock()
    mock_popup.chk_vlc = False
    return mock_popup


@pytest.fixture
def boxmain_instance(mock_grid_streams, mock_scrollview, mock_popup, mock_popup_auth):
    """Create BoxMain instance with mocked dependencies"""
    with patch('app.boxmain.PopUpProgress', return_value=mock_popup), \
         patch('app.boxmain.Window'), \
         patch('app.boxmain.Clock'), \
         patch.object(BoxMain, 'refresh_streams_on'), \
         patch.dict('os.environ', {
             'OAUTH_TOKEN': 'test_token',
             'REFRESH_TOKEN': 'test_refresh',
             'USER_ID': 'test_user'
         }):
        boxmain = BoxMain(mod="test")
        boxmain.grid_streams = mock_grid_streams
        boxmain.scrollview_streams = mock_scrollview
        boxmain.checkbox_auto = Mock()
        boxmain.checkbox_auto.active = True
        boxmain.dialog_auth = mock_popup_auth
        return boxmain


class TestBoxMainInitialization:
    def test_initialization_with_test_mode(self, boxmain_instance):
        """Test BoxMain initialization in test mode"""
        assert boxmain_instance.mod == "test"
        # Test that environment variables are read correctly
        assert boxmain_instance.oauth_token is not None
        assert boxmain_instance.refresh_token is not None
        assert boxmain_instance.user_id is not None

    def test_initialization_without_token(self):
        """Test BoxMain initialization without token triggers authentication"""
        with patch('app.boxmain.PopUpProgress'), \
             patch('app.boxmain.Window'), \
             patch('app.boxmain.Clock'), \
             patch.object(BoxMain, 'dialog_authenticate') as mock_auth, \
             patch.dict('os.environ', {}, clear=True):
            # Ensure oauth_token is None/falsy
            with patch.object(BoxMain, 'oauth_token', None):
                boxmain = BoxMain(mod="prod")
                mock_auth.assert_called_once()


class TestGridColumnsUpdate:
    # def test_update_grid_cols_no_grid(self, boxmain_instance):
    #     """Test update_grid_cols when grid_streams is None"""
    #     # Set grid_streams to None by patching the property
    #     with patch.object(boxmain_instance, 'grid_streams', None):
    #         # Should not raise an exception
    #         boxmain_instance.update_grid_cols(boxmain_instance, 1000)

    def test_update_grid_cols_calculates_columns(self, boxmain_instance):
        """Test grid column calculation based on width"""
        with patch('kivy.metrics.dp', return_value=350):
            boxmain_instance.update_grid_cols(boxmain_instance, 1400)  # Should be 4 columns
            assert boxmain_instance.grid_streams.cols == 4

    def test_update_grid_cols_clamps_values(self, boxmain_instance):
        """Test grid column clamping between 1 and 5"""
        with patch('kivy.metrics.dp', return_value=350):
            # Test minimum (1 column)
            boxmain_instance.update_grid_cols(boxmain_instance, 100)
            assert boxmain_instance.grid_streams.cols == 1

            # Test maximum (5 columns)
            boxmain_instance.update_grid_cols(boxmain_instance, 3000)
            assert boxmain_instance.grid_streams.cols == 5

    def test_update_grid_cols_no_change_needed(self, boxmain_instance):
        """Test when no column change is needed"""
        boxmain_instance.grid_streams.cols = 3
        with patch('kivy.metrics.dp', return_value=350):
            # Width 1000 should give ~2-3 columns, so no change from current 3
            boxmain_instance.update_grid_cols(boxmain_instance, 1200)
            assert boxmain_instance.grid_streams.cols == 3


class TestKeyboardHandling:
    def test_keyboard_down_scroll_down(self, boxmain_instance, mock_scrollview):
        """Test keyboard down arrow scrolling"""
        mock_scrollview.vbar = [0.1, 0.3]  # Not at bottom
        mock_scrollview.scroll_y = 0.5

        result = boxmain_instance._on_keyboard_down(None, (107, 'down'), None, [])

        assert mock_scrollview.scroll_y == 0.4  # Decreased by 0.1
        assert result is True

    def test_keyboard_up_scroll_up(self, boxmain_instance, mock_scrollview):
        """Test keyboard up arrow scrolling"""
        mock_scrollview.vbar = [0.9, 0.3]  # Not at top
        mock_scrollview.scroll_y = 0.5

        result = boxmain_instance._on_keyboard_down(None, (108, 'up'), None, [])

        assert mock_scrollview.scroll_y == 0.6  # Increased by 0.1
        assert result is True

    def test_keyboard_scroll_boundaries(self, boxmain_instance, mock_scrollview):
        """Test keyboard scrolling respects boundaries"""
        # At bottom - should not scroll down
        mock_scrollview.vbar = [0.0, 0.3]
        mock_scrollview.scroll_y = 0.0
        boxmain_instance._on_keyboard_down(None, (107, 'down'), None, [])
        assert mock_scrollview.scroll_y == 0.0

        # At top - should not scroll up
        mock_scrollview.vbar = [1.0, 0.3]
        mock_scrollview.scroll_y = 1.0
        boxmain_instance._on_keyboard_down(None, (108, 'up'), None, [])
        assert mock_scrollview.scroll_y == 1.0


class TestLogout:
    def test_logout_clears_data_and_authenticates(self, boxmain_instance, mock_grid_streams):
        """Test logout clears all data and triggers authentication"""
        with patch('app.boxmain.set_token') as mock_set_token, \
             patch.object(boxmain_instance, 'dialog_authenticate') as mock_auth:
            boxmain_instance.list_streams_on = ['stream1', 'stream2']

            boxmain_instance.logout()

            mock_set_token.assert_called_once_with(
                access_token="",
                refresh_token="",
                user_id=""
            )
            assert boxmain_instance.list_streams_on == []
            mock_grid_streams.clear_widgets.assert_called()
            mock_auth.assert_called_once()


class TestAddMoreStreams:
    def test_add_more_streams_when_needed(self, boxmain_instance, mock_grid_streams):
        """Test adding more streams when grid has fewer than available"""
        boxmain_instance.list_streams_on = ['stream1', 'stream2', 'stream3', 'stream4']
        mock_grid_streams.children = ['existing_widget']  # 1 existing widget

        with patch('app.boxmain.BoxStream') as mock_boxstream:
            boxmain_instance.add_more_streams()

            # Should add 3 more streams (up to 9 total, but only 3 available)
            assert mock_boxstream.call_count == 3
            assert mock_grid_streams.add_widget.call_count == 3

    def test_add_more_streams_no_more_available(self, boxmain_instance, mock_grid_streams):
        """Test no streams added when grid has all available streams"""
        boxmain_instance.list_streams_on = ['stream1', 'stream2']
        mock_grid_streams.children = ['widget1', 'widget2']  # Same number

        boxmain_instance.add_more_streams()

        mock_grid_streams.add_widget.assert_not_called()


class TestAuthentication:
    # def test_dialog_authenticate_creates_popup_and_server(self):
    #     """Test authentication dialog creation"""
    #     # This test is difficult to mock due to import structure
    #     pass

    def test_check_for_token_detects_new_token(self, boxmain_instance):
        """Test token detection and processing"""
        with patch('dotenv.load_dotenv'), \
             patch.dict('os.environ', {'OAUTH_TOKEN': 'new_token', 'REFRESH_TOKEN': 'new_refresh', 'USER_ID': 'new_user'}), \
             patch.object(boxmain_instance, 'refresh_streams_on') as mock_refresh, \
             patch('app.boxmain.UrlRequest') as mock_url_request:
            boxmain_instance.oauth_token = 'old_token'

            result = boxmain_instance.check_for_token(1.0)

            assert boxmain_instance.oauth_token == 'new_token'
            assert boxmain_instance.refresh_token == 'new_refresh'
            assert boxmain_instance.user_id == 'new_user'
            mock_refresh.assert_called_once()
            mock_url_request.assert_called_once_with("http://localhost:5000/shutdown")
            assert result is False  # Should stop the schedule

    def test_check_for_token_no_change(self, boxmain_instance):
        """Test when no token change is detected"""
        boxmain_instance.oauth_token = 'same_token'
        with patch('dotenv.load_dotenv'), \
             patch.dict('os.environ', {'OAUTH_TOKEN': 'same_token'}):
            result = boxmain_instance.check_for_token(1.0)
            assert result is True  # Should continue the schedule

    def test_authenticate_test_mode(self, boxmain_instance):
        """Test authentication in test mode"""
        with patch.object(boxmain_instance, 'refresh_streams_on') as mock_refresh:
            boxmain_instance.mod = "test"
            boxmain_instance.authenticate(None)

            mock_refresh.assert_called_once()

    def test_authenticate_unauthorized_token(self, boxmain_instance):
        """Test authentication with unauthorized token"""
        boxmain_instance.mod = "prod"  # Change to prod mode to trigger refresh logic
        with patch('app.boxmain.UrlRequest') as mock_url_request:
            boxmain_instance.authenticate(None, {"error": "Unauthorized"})

            mock_url_request.assert_called_once()

    def test_authenticate_save_new_token(self, boxmain_instance):
        """Test saving new token from dialog"""
        boxmain_instance.mod = "prod"  # Change to prod mode to trigger token saving logic
        mock_dialog = Mock()
        mock_content = Mock()
        mock_token_field = Mock()
        mock_token_field.text = "token.refresh.user"
        mock_content.children = [Mock()]
        mock_content.children[0].children = [Mock()]
        mock_content.children[0].children[0].ids = Mock()
        mock_content.children[0].children[0].ids.token = mock_token_field
        mock_dialog.ids = Mock()
        mock_dialog.ids.content_container = mock_content

        boxmain_instance.dialog_auth = mock_dialog

        with patch.object(boxmain_instance, 'save_token') as mock_save:
            boxmain_instance.authenticate(None, {})

            mock_save.assert_called_once_with(data={
                "access_token": "token",
                "refresh_token": "refresh",
                "user_id": "user"
            })


class TestTokenSaving:
    def test_save_token_success(self, boxmain_instance):
        """Test successful token saving"""
        test_data = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "user_id": "new_user"
        }

        with patch('app.boxmain.set_token') as mock_set_token, \
             patch.object(boxmain_instance, 'refresh_streams_on') as mock_refresh:
            boxmain_instance.save_token(data=test_data)

            mock_set_token.assert_called_once_with(
                access_token="new_token",
                refresh_token="new_refresh",
                user_id="new_user"
            )
            assert boxmain_instance.oauth_token == "new_token"
            assert boxmain_instance.refresh_token == "new_refresh"
            assert boxmain_instance.user_id == "new_user"
            mock_refresh.assert_called_once()

    def test_save_token_invalid_refresh_token(self, boxmain_instance):
        """Test handling of invalid refresh token"""
        test_data = {"message": "Invalid refresh token"}

        with patch.object(boxmain_instance, 'dialog_authenticate') as mock_auth:
            boxmain_instance.save_token(data=test_data)

            mock_auth.assert_called_once()

    def test_save_token_string_data(self, boxmain_instance):
        """Test token saving with string JSON data"""
        import json
        test_data = {
            "access_token": "token",
            "refresh_token": "refresh",
            "user_id": "user"
        }

        with patch('app.boxmain.set_token') as mock_set_token:
            boxmain_instance.save_token(data=json.dumps(test_data))

            mock_set_token.assert_called_once_with(
                access_token="token",
                refresh_token="refresh",
                user_id="user"
            )


class TestBottomTopScrolling:
    def test_bottomtop_scroll_to_top(self, boxmain_instance, mock_scrollview):
        """Test bottomtop scrolling to top when near bottom"""
        mock_scrollview.vbar = [0.8, 0.3]  # Near bottom
        boxmain_instance.bottomtop()
        assert mock_scrollview.scroll_y == 0

    def test_bottomtop_scroll_to_bottom(self, boxmain_instance, mock_scrollview):
        """Test bottomtop scrolling to bottom when near top"""
        mock_scrollview.vbar = [0.1, 0.3]  # Near top
        boxmain_instance.bottomtop()
        assert mock_scrollview.scroll_y == 1


class TestStreamRefresh:
    def test_refresh_streams_on_test_mode(self, boxmain_instance, mock_popup):
        """Test stream refresh in test mode"""
        boxmain_instance.mod = "test"

        boxmain_instance.refresh_streams_on()

        assert boxmain_instance.list_streams_on == fake_list_streams
        mock_popup.open.assert_called_once()

    def test_refresh_streams_on_with_token(self, boxmain_instance, mock_popup):
        """Test stream refresh with valid token"""
        boxmain_instance.mod = "prod"
        boxmain_instance.oauth_token = "valid_token"
        boxmain_instance.user_id = "user123"

        with patch('app.boxmain.UrlRequest') as mock_url_request:
            boxmain_instance.refresh_streams_on()

            mock_url_request.assert_called_once()
            mock_popup.open.assert_called_once()

    def test_on_list_streams_on_updates_grid(self, boxmain_instance, mock_grid_streams, mock_popup):
        """Test stream list update triggers grid population"""
        test_streams = [{"name": "stream1"}, {"name": "stream2"}]
        boxmain_instance.list_streams_on = test_streams

        with patch('app.boxmain.Clock') as mock_clock, \
             patch('app.boxmain.BoxStream') as mock_boxstream:
            boxmain_instance.on_list_streams_on(boxmain_instance, test_streams)

            mock_popup.dismiss.assert_called()
            mock_grid_streams.clear_widgets.assert_called()
            mock_clock.schedule_once.assert_called()


class TestStreamPlayback:
    def test_play_auto_quality(self, boxmain_instance, mock_popup):
        """Test stream playback with auto quality"""
        boxmain_instance.checkbox_auto.active = True

        with patch('app.boxmain.Popen') as mock_popen:
            boxmain_instance.play("testchannel", "best")

            mock_popup.chk_vlc = True
            mock_popup.open.assert_called_once()
            mock_popen.assert_called_once_with(
                'streamlink http://twitch.tv/testchannel best',
                close_fds=True,
                shell=True
            )

    def test_play_manual_quality_selection(self, boxmain_instance):
        """Test stream playback triggers resolution selection"""
        boxmain_instance.checkbox_auto.active = False

        with patch('app.boxmain.Thread') as mock_thread:
            boxmain_instance.play("testchannel", "best")

            mock_thread.assert_called_once()

    def test_search_resolutions(self, boxmain_instance):
        """Test resolution search functionality"""
        mock_streams = {"720p": Mock(), "1080p": Mock(), "best": Mock(), "worst": Mock()}

        with patch('app.boxmain.Streamlink') as mock_streamlink_class, \
             patch.object(boxmain_instance, 'dialog_select_resolution') as mock_dialog:
            mock_streamlink = Mock()
            mock_streamlink.streams.return_value = mock_streams
            mock_streamlink_class.return_value = mock_streamlink

            boxmain_instance.search_resolutions("testchannel")

            mock_streamlink.streams.assert_called_once_with("https://www.twitch.tv/testchannel")
            mock_dialog.assert_called_once_with(list_r=["720p", "1080p"])

    @patch('app.boxmain.DialogSelectResolution')
    def test_dialog_select_resolution_creates_dialog(self, mock_dialog_class, boxmain_instance, mock_popup):
        """Test resolution selection dialog creation"""
        test_resolutions = ["720p", "1080p"]

        boxmain_instance.dialog_select_resolution.__wrapped__(boxmain_instance, test_resolutions)

        mock_popup.dismiss.assert_called_once()
        mock_dialog_class.assert_called_once()

    def test_play_with_resolution(self, boxmain_instance, mock_popup):
        """Test playing with selected resolution"""
        boxmain_instance.go = "testchannel"
        boxmain_instance.dialog = Mock()

        with patch.object(boxmain_instance, 'play') as mock_play:
            boxmain_instance.play_with_resolution("1080p")

            mock_play.assert_called_once_with(go="testchannel", qlt="1080p")
            boxmain_instance.dialog.dismiss.assert_called_once()


class TestDialogManagement:
    def test_close_dialog(self, boxmain_instance):
        """Test dialog closing functionality"""
        mock_dialog = Mock()
        boxmain_instance.dialog = mock_dialog

        boxmain_instance.close_dialog(None)

        mock_dialog.dismiss.assert_called_once()