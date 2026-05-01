from kivymd.uix.card import MDCard
from kivy.properties import ObjectProperty, StringProperty
from kivy.animation import Animation

class BoxStream(MDCard):
    label_status = ObjectProperty(None)
    preview_img = StringProperty("")
    channel_name = StringProperty("")
    game = StringProperty("")
    viewers_count = StringProperty("")
    stream = StringProperty("")
    status = StringProperty("")

    def __init__(self, channel_data, **kwargs):
        super().__init__(**kwargs)
        self.status = channel_data["channel_status"]
        self.stream = channel_data["channel_name"]
        self.preview_img = channel_data["preview_img"]
        self.channel_name = channel_data["channel_name"].capitalize()
        self.game = channel_data["game"]
        self.viewers_count = "{:,}".format(channel_data["viewers"]).replace(",", ".")

    def info(self, *args):
        if self.ids.label_status.opacity == 0:
            self.ids.label_status.text = self.status
            anim = Animation(opacity=1, duration=0.2)
        else:
            anim = Animation(opacity=0, duration=0.2)

        anim.start(self.ids.label_status)