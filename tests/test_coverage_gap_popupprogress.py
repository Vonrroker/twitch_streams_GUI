from unittest.mock import Mock, patch
from app.components.PopUpProgress.pop_up_progress import PopUpProgress
from kivy.app import App
from kivymd.app import MDApp
import pytest

class DummyMDApp(MDApp):
    pass

@pytest.fixture(autouse=True)
def md_app():
    previous_app = App._running_app
    app = DummyMDApp()
    App._running_app = app
    yield app
    App._running_app = previous_app

def test_pop_up_progress_vlc_changed_on_open():
    """Test PopUpProgress closes if VLC count changes during on_open."""
    with patch("app.components.PopUpProgress.pop_up_progress.process_iter") as mock_iter:
        # Initial call in __init__ returns 0 VLCs
        mock_iter.return_value = []
        
        popup = PopUpProgress(chk_vlc=True)
        assert popup.vlcs == 0
        
        # Second call in on_open returns 1 VLC
        mock_vlc = Mock()
        mock_vlc.info = {"name": "vlc.exe"}
        mock_iter.return_value = [mock_vlc]
        
        with patch.object(popup, "dismiss") as mock_dismiss:
            popup.on_open()
            mock_dismiss.assert_called_once()
            assert popup.chk_vlc is False

def test_pop_up_progress_vlc_changed_in_next():
    """Test PopUpProgress closes if VLC count changes in next()."""
    with patch("app.components.PopUpProgress.pop_up_progress.process_iter") as mock_iter:
        # Initial call in __init__
        mock_iter.return_value = []
        popup = PopUpProgress(chk_vlc=True)
        
        # In next() returns 1 VLC
        mock_vlc = Mock()
        mock_vlc.info = {"name": "vlc.exe"}
        mock_iter.return_value = [mock_vlc]
        
        with patch.object(popup, "dismiss") as mock_dismiss:
            result = popup.next(0.5)
            mock_dismiss.assert_called_once()
            assert popup.chk_vlc is False
            assert result is False
