from os import environ
from kivy.config import Config

Config.set("graphics", "window_state", "maximized")
Config.set("graphics", "minimum_width", 800)
Config.set("graphics", "minimum_height", 384)

from kivymd.app import MDApp
from app.boxmain import BoxMain


class MyApp(MDApp):
    title = "Streams no VLC"
    mod = environ.get("KIVY_ENV", default="prod")

    def build(self):
        self.theme_cls.theme_style = "Dark"  # "Light"
        self.load_all_kv_files(self.directory)

        return BoxMain(mod=self.mod)


if __name__ == "__main__":
    MyApp().run()
