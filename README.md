# Twitch Streams GUI & TUI

A multi-interface desktop application developed in Python that allows you to view and watch live Twitch streams you follow, utilizing [VLC](https://www.videolan.org/vlc/) as the player via [Streamlink](https://streamlink.github.io/).

## 🚀 Features

- **Dual Interfaces:**
  - **GUI Mode:** Modern Material Design interface built with [KivyMD](https://github.com/kivymd/KivyMD).
  - **TUI Mode:** Terminal User Interface for power users, built with [Textual](https://textual.textualize.io/).
- **Automated Authentication:** Integrated local FastAPI server for a seamless OAuth2 login flow.
- **Stream Overview:** View all followed live streams with channel names, games, viewer counts, and status titles.
- **VLC Integration:** Watch streams directly in VLC with high performance and low overhead.
- **Flexible Quality:** Choose specific stream resolutions or toggle "Auto-Best" to launch instantly in the highest quality.

## 🛠️ Requirements

- **Python:** >= 3.12
- **VLC Media Player:** Must be installed and available in your system's PATH.
- **Twitch Developer Credentials:** A Client ID and Secret from the [Twitch Dev Console](https://dev.twitch.tv/console).

## 📥 Installation

Using [uv](https://github.com/astral-sh/uv) (recommended):
```bash
uv sync
```

Alternatively, using pip:
```bash
pip install .
```

## 🏁 How to Run

### GUI Mode (Default)
```bash
python main.py
```

### TUI Mode (Terminal)
```bash
python main.py --tui
```

#### TUI Keybindings:
- `q`: Quit.
- `r`: Refresh stream list.
- `b`: Toggle "Auto-Best" resolution.
- `Enter`: Play selected stream.
- `Esc`: Cancel resolution selection.

## ⚙️ Configuration

Create a file named `.env` inside the `app/` directory with the following content:

```env
client_id=YOUR_TWITCH_CLIENT_ID
TWITCH_SECRET=YOUR_TWITCH_CLIENT_SECRET
CALLBACK_URL=http://localhost:5000/auth/twitch/callback
```

*Note: In the Twitch Dev Console, ensure your Redirect URI is set to `http://localhost:5000/auth/twitch/callback`.*

## 🔐 Authentication Flow

1. On first run, the app will prompt for authentication.
2. It launches a local server and opens your browser to Twitch.
3. Once authorized, tokens are automatically saved to `app/.env`.
4. The app refreshes and displays your followed live streams.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
