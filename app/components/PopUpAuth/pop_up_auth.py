from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog

class PopUpAuth(MDDialog):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.title.color = [1, 1, 1, 1]


class Content(MDBoxLayout):
    ...
