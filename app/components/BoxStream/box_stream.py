from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import ObjectProperty
from kivy.core.window import Window

class BoxStream(MDBoxLayout):
    button_image_channel = ObjectProperty(None)
    label_channel_infos = ObjectProperty(None)
    button_show_status = ObjectProperty(None)
    label_status = ObjectProperty(None)

    def __init__(self, channel_data, **kwargs):
        super().__init__(**kwargs)
        self.height = ((Window.size[0] - 60) / 3) / 1.81
        self.status = channel_data["channel_status"]
        self.stream = channel_data["channel_name"]
        self.button_image_channel.source = channel_data["preview_img"]
        self.label_channel_infos.text = "{} - {} - {:,}".format(
            channel_data["channel_name"].capitalize(),
            channel_data["game"],
            channel_data["viewers"],
        ).replace(",", ".")

        Window.bind(on_resize=self.resize)

    def info(self, *args):
        print("\n\n#########\n\n")
        if self.status in self.label_status.text:
            self.label_status.text = ""

        else:
            self.label_status.text = self.status

    def resize(self, *args):
        self.height = ((Window.size[0] - 60) / 3) / 1.81