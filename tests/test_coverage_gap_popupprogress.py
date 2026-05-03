from unittest.mock import Mock, patch
from app.components.PopUpProgress.pop_up_progress import PopUpProgress
from kivy.app import App
from kivymd.app import MDApp
import pytest
import time

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

def test_pop_up_progress_timeout():
    """Test PopUpProgress closes after 60 seconds timeout."""
    with patch("app.components.PopUpProgress.pop_up_progress.process_iter") as mock_iter:
        mock_iter.return_value = []
        popup = PopUpProgress(chk_vlc=True)
        
        # Use a controlled time mock
        current_time = [100.0]
        def mock_time():
            return current_time[0]

        with patch("time.time", side_effect=mock_time):
            popup.on_open() # Sets start_time to 100
            
            # Simulate 61 seconds passing
            current_time[0] = 161.0
            
            with patch.object(popup, "dismiss") as mock_dismiss:
                result = popup.next(0.5) # Compares current time (161) - start_time (100) = 61
                assert result is False
                mock_dismiss.assert_called_once()
                assert popup.chk_vlc is False

def test_pop_up_progress_logged_once():
    """Test PopUpProgress logs the check message only once."""
    with patch("app.components.PopUpProgress.pop_up_progress.process_iter") as mock_iter:
        mock_iter.return_value = []
        popup = PopUpProgress(chk_vlc=True)
        
        with patch("app.components.PopUpProgress.pop_up_progress.Logger") as mock_logger:
            popup.next(0.5)
            assert popup.logged_check is True
            # Verify Logger.info was called with the check message
            mock_logger.info.assert_any_call("Running periodic process check.")
            
            mock_logger.reset_mock()
            popup.next(0.5)
            # Ensure it wasn't called again
            for call in mock_logger.info.call_args_list:
                assert call[0][0] != "Running periodic process check."
