import pytest
from unittest.mock import patch, MagicMock
from app.config import set_token, env_path

@patch("app.config.set_key")
@patch("app.config.load_dotenv")
def test_set_token(mock_load_dotenv, mock_set_key):
    set_token("access", "refresh", "user")
    
    mock_set_key.assert_any_call(env_path, "OAUTH_TOKEN", "access")
    mock_set_key.assert_any_call(env_path, "REFRESH_TOKEN", "refresh")
    mock_set_key.assert_any_call(env_path, "USER_ID", "user")
    
    mock_load_dotenv.assert_called_with(env_path)
