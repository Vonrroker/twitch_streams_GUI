from kivy.config import Config

Config.set("graphics", "window_state", "maximized")
Config.set("graphics", "minimum_width", 683)
Config.set("graphics", "minimum_height", 384)

from kivymd.app import MDApp
from boxmain import BoxMain


class App(MDApp):
    title = "Streams no VLC"
    # mod = "DEVELOPMENT"
    mod = "TEST"

    def build(self):
        self.theme_cls.theme_style = "Dark"  # "Light"
        return BoxMain(mod=self.mod)


if __name__ == "__main__":
    App().run()
