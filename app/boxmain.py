import sys
import webbrowser
from json import loads
from os import environ
from subprocess import Popen
from threading import Thread

from pprint import pprint
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest
from kivy.properties import ListProperty, ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem
from app.components.BoxStream.box_stream import BoxStream
from app.components.PopUpProgress.pop_up_progress import PopUpProgress
from app.components.DialogSelectResolution.dialog_sselect_resolution import (
    DialogSelectResolution,
    ItemConfirm,
)
from app.components.PopUpAuth.pop_up_auth import PopUpAuth, Content
from kivymd.uix.textfield import MDTextField
from streamlink import Streamlink

from app.config import envs, set_token
from app.tests.fakes.list_streams import fake_list_streams
from app.utils.parser_streams import parser

base_auth_url = "https://auth-token-stream.herokuapp.com"


class BoxMain(MDBoxLayout):
    button_refresh = ObjectProperty(None)
    button_bottomtop = ObjectProperty(None)
    checkbox_auto = ObjectProperty(None)
    scrollview_streams = ObjectProperty(None)
    grid_streams = ObjectProperty(None)
    checkbox_resolution = ObjectProperty(None)
    list_streams_on = ListProperty()
    oauth_token = environ.get("OAUTH_TOKEN", default="")
    refresh_token = environ.get("REFRESH_TOKEN", default="")
    client_id = envs["client_id"]

    def __init__(self, mod, **kwargs):
        super().__init__(**kwargs)
        # self.popup_auth = PopUpAuth()
        self.mod = mod
        self.popup = PopUpProgress()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, "text")
        if self._keyboard.widget:
            # If it exists, this widget is a VKeyboard object which you can use
            # to change the keyboard layout.
            pass
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.button_bottomtop.bind(on_press=self.bottomtop)
        self.scrollview_streams.bind(on_scroll_stop=self.add_more_streams)
        self.scrollview_streams.bind(on_scroll_start=lambda *args: pprint(args[1]))
        if self.mod != "test" and (not self.client_id or not self.oauth_token):
            self.dialog_authenticate()
        else:
            self.refresh_streams_on()

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print("The key", keycode, "have been pressed")
        print(" - text is %r" % text)
        print(" - modifiers are %r" % modifiers)

        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[1] == "down" and self.scrollview_streams.vbar[0] > 0:
            print(self.scrollview_streams.vbar[0])
            if self.scrollview_streams.scroll_y > 0:
                self.scrollview_streams.scroll_y -= 0.1
        if keycode[1] == "up" and self.scrollview_streams.vbar[0] < 1:
            print(self.scrollview_streams.vbar[0])
            if self.scrollview_streams.scroll_y < 1:
                self.scrollview_streams.scroll_y += 0.1

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True

    def logout(self):
        set_token(
            access_token="",
            refresh_token="",
        )
        self.list_streams_on.clear()
        self.grid_streams.clear_widgets()
        self.dialog_authenticate()

    def add_more_streams(self, instance, value):
        # print(instance.vbar[0])
        scroll_pos = instance.vbar[0]
        grid_size = len(self.grid_streams.children)
        if scroll_pos < 0.00001 and grid_size < len(self.list_streams_on):
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
                        f"{base_auth_url}/auth/twitch"
                    ),
                ),
            ],
        )
        # self.dialog_auth.set_normal_height()
        self.dialog_auth.open()

    def authenticate(self, instance, *args):
        print(instance, args)
        if args and args[0]["error"] == "Unauthorized":
            print("refreshing token")
            UrlRequest(
                url=f"{base_auth_url}/refresh?refresh_token={self.refresh_token}",
                on_success=lambda req, result: self.save_token(
                    instance=req, data=result
                ),
                on_failure=lambda req, result: print("fail"),
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
        print(instance, data)
        if isinstance(data, str):
            response = loads(data)
        else:
            response = data

        if "message" in response and response["message"] == "Invalid refresh token":
            return self.dialog_authenticate()

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
        if self.mod == "test":
            self.list_streams_on.extend(fake_list_streams)
        elif self.oauth_token:
            print("Resquest refresh_streams_on")
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

        self.dialog = DialogSelectResolution(
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
