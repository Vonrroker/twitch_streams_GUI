from os import path, environ
from dotenv import load_dotenv, set_key


project_path = path.realpath
app_path = path.dirname(__file__)
env_path = path.join(app_path, ".env")
load_dotenv(env_path)

envs = {
    "project_path": project_path,
    "app_path": app_path,
    "client_id": "1vbir4oyot8xfyacob5lskwj4i89pj",
}


def set_token(access_token, refresh_token, user_id):
    """
    Save the provided tokens and user ID to the .env file.

    Args:
        access_token (str): The OAuth access token.
        refresh_token (str): The OAuth refresh token.
        user_id (str): The user ID.
    """
    print(f"Saving tokens in {env_path}")
    set_key(env_path, "OAUTH_TOKEN", access_token)
    set_key(env_path, "REFRESH_TOKEN", refresh_token)
    set_key(env_path, "USER_ID", user_id)
    
    load_dotenv(env_path)