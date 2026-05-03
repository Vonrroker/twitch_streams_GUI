from kivy.clock import Clock
from kivy.logger import Logger
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog, MDDialogContentContainer
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from psutil import process_iter


class PopUpProgress(MDDialog):
    def __init__(self, chk_vlc=False, **kwargs):
        super().__init__(**kwargs)
        self.chk_vlc = chk_vlc
        self.auto_dismiss = False

        # Try to set transparency after super().__init__
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0]
        self.shadow_color = [0, 0, 0, 0]

        Logger.info("Initializing PopUpProgress.")
        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        self.vlcs = proc.count("vlc")
        Logger.debug(f"Initial VLC count: {self.vlcs}")

        content = MDBoxLayout(
            MDCircularProgressIndicator(
                size_hint=(None, None),
                size=("48dp", "48dp"),
                pos_hint={"center_x": .5, "center_y": .5}
            ),
            orientation="vertical",
            adaptive_height=True,
            padding="24dp"
        )
        content.theme_bg_color = "Custom"
        content.md_bg_color = [0, 0, 0, 0]

        container = MDDialogContentContainer()
        container.add_widget(content)

        self.add_widget(container)

    def on_open(self):
        Logger.info("PopUpProgress opened.")
        if self.chk_vlc:
            Logger.info("VLC monitoring enabled.")
            Clock.schedule_interval(self.next, 0.5)
        else:
            Logger.info("VLC monitoring disabled.")
            Clock.unschedule(self.next)

        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")
        Logger.debug(f"VLC count in on_open: {checking}")

        if checking != self.vlcs:
            Logger.info("VLC count changed. Closing PopUpProgress.")
            self.dismiss()
            self.chk_vlc = False
            return False


    def next(self, dt):
        Logger.info("Running periodic process check.")
        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")
        # Logger.debug(f"Process list in next: {proc}")
        Logger.debug(f"VLC count in next: {checking}")

        if checking != self.vlcs:
            Logger.info("VLC count changed. Closing PopUpProgress.")
            self.dismiss()
            self.chk_vlc = False
            return False
