import pytest
from unittest.mock import Mock, patch, MagicMock
from kivy.app import App
from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from app.boxmain import BoxMain

class DummyMDApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls = ThemeManager()

@pytest.fixture(autouse=True)
def md_app():
    previous_app = App._running_app
    app = DummyMDApp()
    App._running_app = app
    yield app
    App._running_app = previous_app

def test_boxmain_keyboard_widget_hit():
    """Test BoxMain initialization with a keyboard widget."""
    with patch('app.boxmain.PopUpProgress'), \
         patch('app.boxmain.Window') as mock_window, \
         patch('app.boxmain.Clock'), \
         patch.object(BoxMain, 'refresh_streams_on'):
        
        mock_keyboard = Mock()
        mock_keyboard.widget = Mock() # Make it truthy
        mock_window.request_keyboard.return_value = mock_keyboard
        
        boxmain = BoxMain(mod="test")
        assert boxmain._keyboard.widget is not None

def test_boxmain_update_grid_cols_hits_info():
    """Test update_grid_cols hits the Logger.info when cols change."""
    with patch('app.boxmain.PopUpProgress'), \
         patch('app.boxmain.Window'), \
         patch('app.boxmain.Clock'), \
         patch.object(BoxMain, 'refresh_streams_on'):
        
        boxmain = BoxMain(mod="test")
        boxmain.grid_streams = Mock()
        boxmain.grid_streams.cols = 1
        
        with patch('kivy.metrics.dp', return_value=100), \
             patch('app.boxmain.Logger') as mock_logger:
            
            boxmain.update_grid_cols(boxmain, 400) # Should be 4 cols
            
            assert boxmain.grid_streams.cols == 4
            mock_logger.info.assert_called()

def test_boxmain_check_for_token_hits_all():
    """Test check_for_token hits all lines when a new token is found."""
    with patch('app.boxmain.PopUpProgress'), \
         patch('app.boxmain.Window'), \
         patch('app.boxmain.Clock'), \
         patch.object(BoxMain, 'refresh_streams_on'):
        
        boxmain = BoxMain(mod="test")
        boxmain.oauth_token = "old_token"
        boxmain.dialog_auth = Mock()
        
        with patch('dotenv.load_dotenv'), \
             patch('app.boxmain.environ', {
                 'OAUTH_TOKEN': 'new_token',
                 'REFRESH_TOKEN': 'new_refresh',
                 'USER_ID': 'new_user'
             }), \
             patch('app.boxmain.UrlRequest') as mock_url_request:
            
            result = boxmain.check_for_token(0.5)
            
            assert result is False
            assert boxmain.oauth_token == "new_token"
            boxmain.dialog_auth.dismiss.assert_called_once()
            mock_url_request.assert_called_with("http://localhost:5000/shutdown")

def test_boxmain_authenticate_unauthorized():
    """Test authenticate with Unauthorized error."""
    with patch('app.boxmain.PopUpProgress'), \
         patch('app.boxmain.Window'), \
         patch('app.boxmain.Clock'), \
         patch.object(BoxMain, 'refresh_streams_on'):
        
        boxmain = BoxMain(mod="prod")
        boxmain.refresh_token = "some_refresh"
        
        with patch('app.boxmain.UrlRequest') as mock_url_request:
            boxmain.authenticate(None, {"error": "Unauthorized"})
            mock_url_request.assert_called_once()
            args, kwargs = mock_url_request.call_args
            assert "refresh?refresh_token=some_refresh" in kwargs["url"]
