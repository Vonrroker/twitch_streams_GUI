import pytest
from app.utils.parser_streams import parser

def test_parser_success():
    mock_data = (
        None, # First element is ignored according to parser logic: stream_data[1]["data"]
        {
            "data": [
                {
                    "user_name": "Channel1",
                    "game_name": "Game1",
                    "viewer_count": 100,
                    "title": "Title1",
                    "thumbnail_url": "https://test.com/img-{width}x{height}.jpg"
                }
            ]
        }
    )
    
    result = parser(mock_data)
    assert len(result) == 1
    assert result[0]["channel_name"] == "Channel1"
    assert result[0]["preview_img"] == "https://test.com/img.jpg"

def test_parser_empty():
    mock_data = (None, {"data": []})
    result = parser(mock_data)
    assert result == []
