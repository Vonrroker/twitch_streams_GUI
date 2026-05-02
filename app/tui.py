import asyncio
import webbrowser
import subprocess
from os import environ
from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Button, Switch, Label
from textual.screen import ModalScreen
from textual.containers import Grid, Vertical, Horizontal
from textual.binding import Binding

from app.utils.twitch_api import TwitchAPI
from app.auth_server.server import run_server
from app.config import envs, env_path

class ResolutionSelect(ModalScreen[str]):
    """Modal screen to select stream resolution."""
    BINDINGS = [Binding("escape", "dismiss(None)", "Cancel")]
    
    DEFAULT_CSS = """
    ResolutionSelect {
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }

    #dialog {
        width: 40;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    Vertical {
        height: auto;
        align: center middle;
    }

    Button {
        width: 100%;
        margin: 0 1;
    }
    """
    
    def __init__(self, resolutions: list[str], channel: str):
        super().__init__()
        self.resolutions = resolutions
        self.channel = channel

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(f"Select resolution for [bold]{self.channel}[/bold]", id="title")
            for res in self.resolutions:
                yield Button(res, variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(str(event.button.label))

    def on_mount(self) -> None:
        # Foca no primeiro botão para permitir navegação com setas
        self.call_after_refresh(self.focus_first_button)

    def focus_first_button(self) -> None:
        buttons = self.query(Button)
        if buttons:
            buttons.first().focus()

    def on_key(self, event: Binding) -> None:
        """Handle arrow keys for navigation within the modal."""
        if event.key == "up":
            self.focus_previous()
        elif event.key == "down":
            self.focus_next()
        elif event.key == "escape":
            self.dismiss(None)

class TwitchTUI(App):
    """Twitch Streams TUI."""
    
    TITLE = "Twitch Streams TUI"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("b", "toggle_best", "Auto-Best"),
    ]
    
    CSS = """
    DataTable {
        height: 1fr;
    }
    #top-bar {
        height: 3;
        background: $surface;
        padding: 0 1;
        align: right middle;
    }
    #top-bar Label {
        margin-right: 1;
        text-style: bold;
    }
    """

    def __init__(self):
        super().__init__()
        self.api = TwitchAPI()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="top-bar"):
            yield Label("Auto-Best Resolution:")
            yield Switch(value=True, id="auto-best")
        yield DataTable(zebra_stripes=True)
        yield Footer()

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("Channel", "Viewers", "Game", "Title")
        await self.refresh_streams()

    async def refresh_streams(self) -> None:
        load_dotenv(env_path)
        self.api = TwitchAPI() # Refresh API state from .env
        
        if not self.api.oauth_token:
            self.notify("Authentication required. Opening browser...", severity="warning")
            await self.authenticate()
            return

        table = self.query_one(DataTable)
        table.clear()
        
        streams = await self.api.get_followed_streams()
        if streams:
            for stream in streams:
                table.add_row(
                    stream["channel_name"],
                    str(stream["viewers"]),
                    stream["game"],
                    stream["channel_status"],
                    key=stream["channel_name"]
                )
        else:
            self.notify("No live streams found or error fetching.", severity="error")

    async def authenticate(self):
        # Start server in a separate thread/task
        asyncio.create_task(asyncio.to_thread(run_server))
        webbrowser.open("http://localhost:5000/auth/twitch")
        
        self.notify("Waiting for authentication...", severity="info")
        
        # Poll for token in .env
        for _ in range(60): # 1 minute timeout
            await asyncio.sleep(2)
            load_dotenv(env_path)
            if environ.get("OAUTH_TOKEN"):
                self.notify("Authentication successful!", severity="information")
                await self.refresh_streams()
                return
        
        self.notify("Authentication timed out.", severity="error")

    async def action_refresh(self) -> None:
        await self.refresh_streams()

    async def action_toggle_best(self) -> None:
        switch = self.query_one("#auto-best", Switch)
        switch.value = not switch.value
        self.notify(f"Auto-Best: {'Enabled' if switch.value else 'Disabled'}")

    async def action_select_stream(self) -> None:
        """Fallback for the 'enter' binding if RowSelected isn't enough."""
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            # We simulate a row selection to reuse the logic
            row_key = table.get_row_at(table.cursor_row)
            await self.handle_row_selection(row_key)

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection (Enter or Click)."""
        await self.handle_row_selection(event.row_key)

    async def handle_row_selection(self, row_key) -> None:
        table = self.query_one(DataTable)
        try:
            row = table.get_row(row_key)
            channel = str(row[0]) 
            await self.play_stream(channel)
        except Exception as e:
            self.notify(f"Error selecting row: {e}", severity="error")

    async def play_stream(self, channel: str):
        auto_best = self.query_one("#auto-best", Switch).value
        
        if auto_best:
            self.run_streamlink(channel, "best")
            return

        self.notify(f"Fetching resolutions for {channel}...")
        
        # Get resolutions using streamlink
        try:
            from streamlink import Streamlink
            session = Streamlink()
            streams = await asyncio.to_thread(session.streams, f"https://www.twitch.tv/{channel}")
            
            resolutions = [res for res in streams.keys() if res not in ("best", "worst")]
            
            if not resolutions:
                self.notify("No resolutions found, playing 'best'.", severity="warning")
                self.run_streamlink(channel, "best")
                return

            def handle_resolution(resolution: str):
                if resolution:
                    self.run_streamlink(channel, resolution)

            self.push_screen(ResolutionSelect(resolutions, channel), handle_resolution)
            
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def run_streamlink(self, channel: str, resolution: str):
        cmd = f"streamlink http://twitch.tv/{channel} {resolution}"
        # Redireciona stdout e stderr para o vazio para não sujar o terminal ao fechar o VLC
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.notify(f"Launching {channel} at {resolution} in VLC...")

if __name__ == "__main__":
    app = TwitchTUI()
    app.run()
