from subprocess import Popen
from threading import Thread
from psutil import process_iter
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivymd.uix.dialog import ModalView
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.clock import mainthread
from streamlink import Streamlink
from credencial import cred
from fakes.list_streams import fake_list_streams


class BoxMain(MDBoxLayout):
    button_refresh = ObjectProperty(None)
    button_bottomtop = ObjectProperty(None)
    checkbox_auto = ObjectProperty(None)
    scrollview_streams = ObjectProperty(None)
    grid_streams = ObjectProperty(None)
    checkbox_resolution = ObjectProperty(None)
    list_streams_on = []

    def __init__(self, mod, **kwargs):
        super().__init__(**kwargs)
        self.mod = mod
        self.popup = PopUpProgress()
        self.refresh_streams_on()
        self.button_bottomtop.bind(on_press=self.bottomtop)

    def bottomtop(self, *args):
        if (self.scrollview_streams.vbar[0]) > (
            1 - (self.scrollview_streams.vbar[0] + self.scrollview_streams.vbar[1])
        ):
            self.scrollview_streams.scroll_y = 0
        else:
            self.scrollview_streams.scroll_y = 1

    def refresh_streams_on(self):
        self.popup.open()
        if self.mod == "TEST":
            self.load_grid_streams(fake_list_streams)
        else:
            UrlRequest(
                url="https://api.twitch.tv/kraken/streams/followed?limit=21",
                req_headers={
                    "Accept": "application/vnd.twitchtv.v5+json",
                    "Client-ID": cred["client_id"],
                    "Authorization": f'OAuth {cred["oauth_token"]}',
                },
                on_success=lambda *args: self.load_grid_streams(
                    data_streams=args[1]["streams"]
                ),
                on_failure=lambda *args: print(args),
            )

    def load_grid_streams(self, data_streams):
        self.popup.dismiss()

        self.list_streams_on = [
            {
                "channel_name": x["channel"]["name"],
                "game": x["game"],
                "viewers": x["viewers"],
                "channel_status": x["channel"]["status"],
                "preview_img": x["preview"]["large"],
            }
            for x in data_streams
        ]
        self.grid_streams.clear_widgets()

        for stream in self.list_streams_on:
            self.grid_streams.add_widget(BoxStream(channel_data=stream))

    def play(self, go: str, qlt="best"):
        self.popup.open()
        self.go = go
        if not self.checkbox_auto.active and qlt == "best":
            Thread(target=self.extrair_resols, args=(go,)).start()
        else:
            self.popup.chk_vlc = True
            self.popup.open()
            try:
                self.popup_resol.dismiss()
            except AttributeError:
                pass
            tmp = f"streamlink http://twitch.tv/{go} {qlt}"
            print(tmp)
            Popen(tmp, close_fds=True, shell=True)

    def extrair_resols(self, go):
        streamlink = Streamlink()
        streams = streamlink.streams(f"https://www.twitch.tv/{go}")
        list_resolution = [i for i in streams]
        if "worst" in list_resolution:
            list_resolution.remove("worst")
        if "best" in list_resolution:
            list_resolution.remove("best")
        self.select_resolution(list_r=list_resolution)

    @mainthread
    def select_resolution(self, list_r):
        self.popup.dismiss()

        self.list_item_confirm = [ItemConfirm(text=item) for item in list_r]

        self.dialog = ResolDialog(
            title="Escolha resolução:",
            # title.color=[0, 1, 0, 1],
            type="confirmation",
            size_hint=(0.7, 1),
            auto_dismiss=False,
            items=self.list_item_confirm,
            buttons=[
                MDFlatButton(text="PLAY", on_release=self.play_with_resolution),
                MDFlatButton(text="CANCELAR", on_release=self.close_dialog),
            ],
        )
        self.dialog.open()

    def play_with_resolution(self, instance):
        for item in self.list_item_confirm:
            if item.checkbox_resolution.active:
                self.play(go=self.go, qlt=item.text)
                self.dialog.dismiss()
                break

    def close_dialog(self, instance):
        self.dialog.dismiss()


class ItemConfirm(OneLineAvatarIconListItem):
    divider = None


class ResolDialog(MDDialog):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.title.color = [1, 1, 1, 1]


class BoxStream(BoxLayout):
    button_image_channel = ObjectProperty(None)
    label_channel_infos = ObjectProperty(None)
    button_show_status = ObjectProperty(None)
    label_status = ObjectProperty(None)

    def __init__(self, channel_data, **kwargs):
        super().__init__(**kwargs)
        self.button_show_status.bind(on_press=self.info)
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

    def info(self, instance):
        if self.status in self.label_status.text:
            self.label_status.text = ""

        else:
            self.label_status.text = self.status

    def resize(self, *args):
        self.height = ((Window.size[0] - 60) / 3) / 1.81


class PopUpProgress(ModalView):
    def __init__(self, chk_vlc=False, **kwargs):
        super().__init__(**kwargs)
        self.chk_vlc = chk_vlc

        proc = [x.info["name"] for x in process_iter(["name"])]

        self.vlcs = proc.count("vlc")

    def on_open(self):
        if self.chk_vlc:
            Clock.schedule_interval(self.next, 0.1)

        proc = [x.info["name"] for x in process_iter(["name"])]
        checking = proc.count("vlc")

        if checking != self.vlcs:
            self.dismiss()
            self.chk_vlc = False
            return False

    def next(self, dt):
        proc = [x.info["name"] for x in process_iter(["name"])]
        checking = proc.count("vlc")

        if checking != self.vlcs:
            self.dismiss()
            self.chk_vlc = False
            return False
