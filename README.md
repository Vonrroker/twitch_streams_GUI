# Twitch Streams GUI

A desktop application developed in Python with a [KivyMD](https://github.com/kivymd/KivyMD) interface that allows you to view and watch live Twitch streams you follow, utilizing [VLC](https://www.videolan.org/vlc/) as the player.

## 🚀 Features

- **Automated Authentication:** Integrated local FastAPI server for a seamless OAuth2 login flow.
- **Stream Overview:** View all followed live streams with thumbnails and viewer counts.
- **VLC Integration:** Watch streams directly in VLC via Streamlink.
- **Resolution Selection:** Choose your preferred stream quality or use "best" by default.
- **Material Design:** Clean and modern interface built with KivyMD.

## 🛠️ Requirements

- **Python:** >= 3.12
- **VLC Media Player:** Must be installed and available in your system's PATH.
- **Twitch Developer Credentials:** You'll need a Client ID and Secret from the [Twitch Dev Console](https://dev.twitch.tv/console).

## 📥 Installation

Using [uv](https://github.com/astral-sh/uv) (recommended):
```bash
uv sync
```

Alternatively, using Poetry:
```bash
poetry install
```

## ⚙️ Configuration

Create a file named `.env` inside the `app/` directory with the following content:

```env
client_id=YOUR_TWITCH_CLIENT_ID
TWITCH_SECRET=YOUR_TWITCH_CLIENT_SECRET
CALLBACK_URL=http://localhost:5000/auth/twitch/callback
```

*Note: In the Twitch Dev Console, ensure your Redirect URI is set to `http://localhost:5000/auth/twitch/callback`.*

## 🏁 How to Run

```bash
# If using uv
uv run main.py

# If using poetry
poetry shell
python main.py
```

## 🔐 How the Authentication Works

1. When you first open the app (or log out), an authentication dialog will appear.
2. Click **"Abrir Link no Navegador"**.
3. Log in to your Twitch account and authorize the application.
4. The local server will automatically capture the tokens and save them to your `.env` file.
5. The application will refresh, the dialog will close, and your streams will appear.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
