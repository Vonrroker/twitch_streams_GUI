from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.dialog.dialog import MDDialog


class ItemConfirm(OneLineAvatarIconListItem):
    divider = None


class DialogSelectResolution(MDDialog):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.title.color = [1, 1, 1, 1]