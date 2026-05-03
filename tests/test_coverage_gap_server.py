import time
from unittest.mock import patch
from app.auth_server.server import run_server, stop_event

def test_run_server_loop_hit():
    """Test run_server loop to ensure time.sleep(0.5) is hit."""
    stop_event.clear()
    
    # We use a counter to set the event after the first sleep
    class SleepCounter:
        def __init__(self):
            self.count = 0
            
        def sleep(self, seconds):
            self.count += 1
            stop_event.set() # Set the event so the loop terminates after this sleep

    counter = SleepCounter()
    
    with patch("uvicorn.Server") as MockServer, \
         patch("uvicorn.Config"), \
         patch("threading.Thread"), \
         patch("time.sleep", side_effect=counter.sleep):
        
        run_server()
        
        assert counter.count > 0
        assert MockServer.return_value.should_exit is True
