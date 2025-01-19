from kivy.clock import Clock
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from psutil import process_iter
from kivymd import images_path


class PopUpProgress(MDDialog):
    def __init__(self, chk_vlc=False, **kwargs):
        super().__init__(**kwargs)
        self.chk_vlc = chk_vlc
        self.background = f'{images_path}/transparent.png'
        self.size_hint = (None, None)
        self.size = (300, 300)
        self.separator_height = 0
        self.auto_dismiss = False

        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        

        self.vlcs = proc.count("vlc")
        # print(proc)
        # print(self.vlcs)
        self.add_widget(MDCircularProgressIndicator(
            size_hint = (None, None),
            size = self.size
        ))

    def on_open(self):
        # print(self.chk_vlc)
        if self.chk_vlc:
            print('entrou')
            Clock.schedule_interval(self.next, 0.1)

        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")
        # print(proc)
        # print(self.vlcs)

        if checking != self.vlcs:
            self.dismiss()
            self.chk_vlc = False
            return False

    def next(self, dt):
        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")
        print(proc)
        print(self.vlcs)

        if checking != self.vlcs:
            self.dismiss()
            self.chk_vlc = False
            return False
