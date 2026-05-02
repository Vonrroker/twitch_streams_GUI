import logging
from kivy.clock import Clock
from psutil import process_iter

from kivymd.uix.dialog import MDDialog, MDDialogContentContainer
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.boxlayout import MDBoxLayout

# Basic logger configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

class PopUpProgress(MDDialog):
    def __init__(self, chk_vlc=False, **kwargs):
        super().__init__(**kwargs)
        self.chk_vlc = chk_vlc
        self.auto_dismiss = False
        
        # Try to set transparency after super().__init__
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0]
        self.shadow_color = [0, 0, 0, 0]

        logging.info("Initializing PopUpProgress.")
        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        self.vlcs = proc.count("vlc")
        logging.debug(f"Initial VLC count: {self.vlcs}")

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
        logging.info("PopUpProgress opened.")
        if self.chk_vlc:
            logging.info("VLC monitoring enabled.")
            Clock.schedule_interval(self.next, 0.5)
        else:
            logging.info("VLC monitoring disabled.")
            Clock.unschedule(self.next)

        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")
        logging.debug(f"VLC count in on_open: {checking}")

        if checking != self.vlcs:
            logging.info("VLC count changed. Closing PopUpProgress.")
            self.dismiss()
            self.chk_vlc = False
            return False
    

    def next(self, dt):
        logging.info("Running periodic process check.")
        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")
        # logging.debug(f"Process list in next: {proc}")
        logging.debug(f"VLC count in next: {checking}")

        if checking != self.vlcs:
            logging.info("VLC count changed. Closing PopUpProgress.")
            self.dismiss()
            self.chk_vlc = False
            return False
