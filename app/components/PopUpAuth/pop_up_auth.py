from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.theming import ThemeManager


class PopUpAuth(MDDialog):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.title.color = self.theme_cls.primary_color


class Content(MDBoxLayout):
    ...
