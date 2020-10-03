from os import path, environ
from dotenv import load_dotenv


app_path = path.dirname(__file__)
env_path = path.join(app_path, ".env")
load_dotenv(env_path)

envs = {
    "app_path": app_path,
    "oauth_token": environ.get("OAUTH_TOKEN"),
    "refresh_token": environ.get("REFRESH_TOKEN"),
    "client_id": "1vbir4oyot8xfyacob5lskwj4i89pj",
}


def set_token(access_token, refresh_token):
    print(access_token, refresh_token)
    with open(env_path, "w") as f:
        f.write(f"OAUTH_TOKEN={access_token}\n")
        f.write(f"REFRESH_TOKEN={refresh_token}")
    load_dotenv(env_path)