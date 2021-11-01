from kivy.clock import Clock
from kivymd.uix.dialog import BaseDialog
from psutil import process_iter

class PopUpProgress(BaseDialog):
    def __init__(self, chk_vlc=False, **kwargs):
        super().__init__(**kwargs)
        self.chk_vlc = chk_vlc

        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]

        self.vlcs = proc.count("vlc")

    def on_open(self):
        if self.chk_vlc:
            Clock.schedule_interval(self.next, 0.1)

        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")

        if checking != self.vlcs:
            self.dismiss()
            self.chk_vlc = False
            return False

    def next(self, dt):
        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")

        if checking != self.vlcs:
            self.dismiss()
            self.chk_vlc = False
            return False
