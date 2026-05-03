from os import environ
import argparse
import sys
import os

# Configure Kivy logger to save logs in .kivy/logs
os.environ["KIVY_HOME"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".kivy")

def run_tui():
    from app.tui import TwitchTUI
    app = TwitchTUI()
    app.run()

def run_gui():
    from kivy.config import Config
    Config.set("graphics", "window_state", "maximized")
    Config.set("graphics", "minimum_width", 800)
    Config.set("graphics", "minimum_height", 384)
    # Aumenta o pool de threads para carregamento de imagens (padrão é 2)
    Config.set("network", "useragent", "Mozilla/5.0")
    from kivy.loader import Loader
    Loader.num_workers = 8

    from kivymd.app import MDApp  # noqa: E402
    from app.boxmain import BoxMain  # noqa: E402

    class MyApp(MDApp):
        title = "Streams no VLC"
        mod = environ.get("KIVY_ENV", default="prod")

        def build(self):
            self.theme_cls.theme_style = "Dark"  # "Light"
            self.load_all_kv_files(self.directory)

            return BoxMain(mod=self.mod)

        def toggle_theme(self):
            self.theme_cls.theme_style = (
                "Dark" if self.theme_cls.theme_style == "Light" else "Light"
            )

    MyApp().run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twitch Streams GUI/TUI")
    parser.add_argument("--tui", action="store_true", help="Run in TUI mode")
    args = parser.parse_args()

    if args.tui:
        run_tui()
    else:
        run_gui()
