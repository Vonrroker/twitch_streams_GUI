import sys
from os import environ
from subprocess import Popen
from threading import Thread
from psutil import process_iter
import webbrowser
from json import loads
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivymd.uix.dialog import ModalView
from kivy.clock import Clock, mainthread
from kivy.properties import ObjectProperty, ListProperty
from streamlink import Streamlink
from utils.parser_streams import parser
from fakes.list_streams import fake_list_streams

from config import envs, set_token


class Content(BoxLayout):
    ...


class BoxMain(MDBoxLayout):
    button_refresh = ObjectProperty(None)
    button_bottomtop = ObjectProperty(None)
    checkbox_auto = ObjectProperty(None)
    scrollview_streams = ObjectProperty(None)
    grid_streams = ObjectProperty(None)
    checkbox_resolution = ObjectProperty(None)
    list_streams_on = ListProperty()
    oauth_token = environ["OAUTH_TOKEN"]
    refresh_token = environ["REFRESH_TOKEN"]
    client_id = envs["client_id"]

    def __init__(self, mod, **kwargs):
        super().__init__(**kwargs)
        # self.popup_auth = PopUpAuth()
        self.mod = mod
        self.popup = PopUpProgress()
        self.button_bottomtop.bind(on_press=self.bottomtop)
        self.scrollview_streams.bind(on_scroll_stop=self.add_more_streams)
        if self.mod != "testing" and (not self.client_id or not self.oauth_token):
            self.dialog_authenticate()
        else:
            self.refresh_streams_on()

    def add_more_streams(self, instance, value):
        # print(instance.vbar[0])
        scroll_pos = instance.vbar[0]
        grid_size = len(self.grid_streams.children)
        if scroll_pos < 0.00001 and grid_size < len(self.list_streams_on):
            print(str(grid_size))
            print(str(len(self.list_streams_on)))
            for stream in self.list_streams_on[grid_size : grid_size + 9]:
                self.grid_streams.add_widget(BoxStream(channel_data=stream))

    @mainthread
    def dialog_authenticate(self):
        self.dialog_auth = PopUpAuth(
            content_cls=Content(),
            buttons=[
                MDFlatButton(
                    text="Fazer autenticação",
                    on_release=self.authenticate,
                ),
                MDFlatButton(
                    text="Abrir Url",
                    on_release=lambda arg: webbrowser.open(
                        "https://auth-token-stream.herokuapp.com/auth/twitch"
                    ),
                ),
            ],
        )
        self.dialog_auth.set_normal_height()
        self.dialog_auth.open()

    def authenticate(self, instance, *args):
        # print(instance, args)
        if args and args[0]["error"] == "Unauthorized":
            print("refreshing token")
            UrlRequest(
                url=f"https://auth-token-stream.herokuapp.com/refresh?refresh_token={self.refresh_token}",
                on_success=lambda req, result: self.save_token(
                    instance=req, data=result
                ),
            )
        else:
            (
                field_token,
                field_refresh_token,
            ) = self.dialog_auth.content_cls.ids.token.text.split(".")
            self.save_token(
                data={
                    "access_token": field_token,
                    "refresh_token": field_refresh_token,
                }
            )
            self.dialog_auth.dismiss()

    def save_token(self, *, instance=None, data):
        # print(instance, data)
        if isinstance(data, str):
            response = loads(data)
        else:
            response = data

        set_token(
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
        )
        self.oauth_token = response["access_token"]
        self.refresh_token = response["refresh_token"]
        self.refresh_streams_on()

    def bottomtop(self, *args):
        if (self.scrollview_streams.vbar[0]) > (
            1 - (self.scrollview_streams.vbar[0] + self.scrollview_streams.vbar[1])
        ):
            self.scrollview_streams.scroll_y = 0
        else:
            self.scrollview_streams.scroll_y = 1

    def refresh_streams_on(self):
        self.list_streams_on.clear()
        self.popup.open()
        if self.mod == "testing":
            self.load_grid_streams(fake_list_streams)
        elif self.oauth_token:
            print(f"Resquest refresh_streams_on com {self.oauth_token}")
            UrlRequest(
                url="https://api.twitch.tv/kraken/streams/followed?stream_type=live&limit=100",
                req_headers={
                    "Accept": "application/vnd.twitchtv.v5+json",
                    "Client-ID": self.client_id,
                    "Authorization": f"OAuth {self.oauth_token}",
                },
                on_success=lambda *response: self.list_streams_on.extend(
                    parser(response)
                ),
                on_failure=self.authenticate,
            )

    def on_list_streams_on(self, instance, value):
        self.popup.dismiss()

        self.grid_streams.clear_widgets()

        for stream in self.list_streams_on[:30]:
            self.grid_streams.add_widget(BoxStream(channel_data=stream))

    def play(self, go: str, qlt="best"):
        self.popup.open()
        self.go = go
        if not self.checkbox_auto.active and qlt == "best":
            Thread(target=self.search_resolutions, args=(go,)).start()
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

    def search_resolutions(self, go):
        streamlink = Streamlink()
        streams = streamlink.streams(f"https://www.twitch.tv/{go}")
        list_resolution = [i for i in streams]
        if "worst" in list_resolution:
            list_resolution.remove("worst")
        if "best" in list_resolution:
            list_resolution.remove("best")
        self.dialog_select_resolution(list_r=list_resolution)

    @mainthread
    def dialog_select_resolution(self, list_r):
        self.popup.dismiss()

        self.list_item_confirm = [ItemConfirm(text=item) for item in list_r]

        self.dialog = ResolDialog(
            title="Escolha resolução:",
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


class PopUpAuth(MDDialog):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.title.color = [1, 1, 1, 1]
