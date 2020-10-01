from os import path, environ
from dotenv import load_dotenv


app_path = path.dirname(__file__)

load_dotenv(path.join(app_path, ".env"))

envs = {
    "app_path": app_path,
    "oauth_token": environ.get("OAUTH_TOKEN"),
    "client_id": "1vbir4oyot8xfyacob5lskwj4i89pj",
}
