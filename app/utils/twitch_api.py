import httpx
import logging
from app.config import envs, set_token
from os import environ

class TwitchAPI:
    def __init__(self):
        self.client_id = envs.get("client_id")
        self.user_id = environ.get("USER_ID")
        self.oauth_token = environ.get("OAUTH_TOKEN")
        self.refresh_token = environ.get("REFRESH_TOKEN")

    async def get_followed_streams(self):
        if not self.oauth_token or not self.user_id:
            return None

        url = f"https://api.twitch.tv/helix/streams/followed?type=live&user_id={self.user_id}"
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.oauth_token}",
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 401:
                    # Token expired, try to refresh
                    if await self.refresh_access_token():
                        # Retry once with new token
                        headers["Authorization"] = f"Bearer {self.oauth_token}"
                        resp = await client.get(url, headers=headers)
                    else:
                        return None

                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    return [
                        {
                            "channel_name": x["user_name"],
                            "game": x["game_name"],
                            "viewers": x["viewer_count"],
                            "channel_status": x["title"],
                        }
                        for x in data
                    ]
            except Exception as e:
                logging.error(f"Error fetching streams: {e}")
        return None

    async def refresh_access_token(self):
        if not self.refresh_token:
            return False

        url = "https://id.twitch.tv/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": environ.get("TWITCH_SECRET"),
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, data=data)
                if resp.status_code == 200:
                    tokens = resp.json()
                    self.oauth_token = tokens["access_token"]
                    self.refresh_token = tokens["refresh_token"]
                    # We need the user_id again, usually it doesn't change
                    # but set_token expects it.
                    set_token(self.oauth_token, self.refresh_token, self.user_id)
                    return True
            except Exception as e:
                logging.error(f"Error refreshing token: {e}")
        return False
