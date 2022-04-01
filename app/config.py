from os import path, environ
from dotenv import load_dotenv


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
    print(f"Salvando tokens em {env_path}")
    with open(env_path, "w") as f:
        f.write(f"OAUTH_TOKEN={access_token}\n")
        f.write(f"REFRESH_TOKEN={refresh_token}\n")
        f.write(f"USER_ID={user_id}")
    load_dotenv(env_path)