import time

from kivy.clock import Clock
from kivy.logger import Logger
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog, MDDialogContentContainer
from kivymd.uix.label import MDLabel
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from psutil import process_iter


class PopUpProgress(MDDialog):
    def __init__(self, chk_vlc=False, **kwargs):
        super().__init__(**kwargs)
        self.chk_vlc = chk_vlc
        self.auto_dismiss = False
        self.start_time = 0
        self.logged_check = False

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
            MDBoxLayout(
                MDLabel(
                    text="Waiting for VLC to open...",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 1], # White text for visibility
                    adaptive_height=True,
                    padding=("0dp", "8dp")
                ),
                theme_bg_color="Custom",
                md_bg_color=[0, 0, 0, 0.7], # Semi-transparent black background
                adaptive_height=True,
                radius=[12, 12, 12, 12], # Rounded corners for polish
                padding="8dp"
            ),
            orientation="vertical",
            adaptive_height=True,
            padding="24dp",
            spacing="16dp"
        )
        content.theme_bg_color = "Custom"
        content.md_bg_color = [0, 0, 0, 0]

        container = MDDialogContentContainer()
        container.add_widget(content)

        self.add_widget(container)

    def on_open(self):
        Logger.info("PopUpProgress opened.")
        self.start_time = time.time()
        self.logged_check = False
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
        if not self.logged_check:
            Logger.info("Running periodic process check.")
            self.logged_check = True

        # Timeout after 60 seconds
        if time.time() - self.start_time > 60:
            Logger.warning("VLC opening timed out after 60 seconds.")
            self.dismiss()
            self.chk_vlc = False
            return False

        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")
        Logger.debug(f"VLC count in next: {checking}")

        if checking != self.vlcs:
            Logger.info("VLC count changed. Closing PopUpProgress.")
            self.dismiss()
            self.chk_vlc = False
            return False
