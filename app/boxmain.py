import sys
import webbrowser
import logging
from json import loads
from os import environ
from subprocess import Popen
from threading import Thread

from pprint import pprint
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivymd.uix.widget import MDWidget
from kivy.uix.widget import Widget
from kivy.network.urlrequest import UrlRequest
from kivy.properties import ListProperty, ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemTrailingCheckbox
from kivymd.uix.dialog import MDDialogHeadlineText, MDDialogButtonContainer, MDDialogContentContainer, MDDialog
from app.components.BoxStream.box_stream import BoxStream
from app.components.PopUpProgress.pop_up_progress import PopUpProgress
from app.components.DialogSelectResolution.dialog_sselect_resolution import (
    DialogSelectResolution,
)
from app.components.PopUpAuth.pop_up_auth import Content, PopUpAuth
from kivymd.uix.textfield import MDTextField
from streamlink import Streamlink

import uvicorn
from app.auth_server.server import app as auth_app, run_server
from app.config import envs, set_token
from tests.fakes.list_streams import fake_list_streams
from app.utils.parser_streams import parser

base_auth_url = "http://localhost:5000"
user_info_url = "https://id.twitch.tv/oauth2/userinfo"

# Configuração básica do logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)


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
    user_id = environ.get("USER_ID")
    client_id = envs["client_id"]

    def __init__(self, mod, **kwargs):
        super().__init__(**kwargs)
        self.mod = mod
        self.popup = PopUpProgress()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, "text")
        if self._keyboard.widget:
            pass
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        
        # Garante que a atualização ocorra após a montagem do layout
        self.bind(width=self.update_grid_cols)
        Clock.schedule_once(lambda dt: self.update_grid_cols(self, self.width))
        
        if self.mod != "test" and (not self.client_id or not self.oauth_token):
            self.dialog_authenticate()
        else:
            self.refresh_streams_on()

    def update_grid_cols(self, instance, width):
        from kivy.metrics import dp
        logging.debug(f"Redimensionando: largura={width}")
        if not self.grid_streams:
            return
            
        # Define uma largura ideal para cada card (ex: 350dp)
        target_column_width = dp(350)
        
        # Calcula quantas colunas cabem, limitando entre 1 e 5
        new_cols = max(1, min(5, int(width / target_column_width)))
            
        if self.grid_streams.cols != new_cols:
            logging.info(f"Alterando grid para {new_cols} colunas (largura: {width}px, alvo: {target_column_width}px)")
            self.grid_streams.cols = new_cols
            logging.info(f"Alterando grid para {new_cols} colunas (largura: {width}px)")
            self.grid_streams.cols = new_cols

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == "down" and self.scrollview_streams.vbar[0] > 0:
            if self.scrollview_streams.scroll_y > 0:
                self.scrollview_streams.scroll_y -= 0.1
        if keycode[1] == "up" and self.scrollview_streams.vbar[0] < 1:
            if self.scrollview_streams.scroll_y < 1:
                self.scrollview_streams.scroll_y += 0.1

        return True

    def logout(self, *args):
        logging.info("Iniciando logout...")
        logging.debug(f"Argumentos recebidos no logout: {args}")
        set_token(
            access_token="",
            refresh_token="",
            user_id=""
        )
        self.list_streams_on.clear()
        self.grid_streams.clear_widgets()
        logging.info("Usuário deslogado com sucesso. Abrindo diálogo de autenticação.")
        self.dialog_authenticate()

    def add_more_streams(self, *args):
        grid_size = len(self.grid_streams.children)
        if grid_size < len(self.list_streams_on):
            logging.info("Adicionando mais streams à grade.")
            for stream in self.list_streams_on[grid_size : grid_size + 9]:
                self.grid_streams.add_widget(BoxStream(channel_data=stream))
                


    @mainthread
    def dialog_authenticate(self):
        logging.info("Abrindo diálogo de autenticação.")
        self.dialog_auth = PopUpAuth(authenticate=self.authenticate, base_auth_url=base_auth_url)
        self.dialog_auth.open()
        
        # Iniciar servidor de autenticação em background
        Thread(target=self.run_auth_server, daemon=True).start()
        
        # Iniciar monitoramento do token no .env
        Clock.schedule_interval(self.check_for_token, 1)

    def run_auth_server(self):
        logging.info("Iniciando servidor FastAPI de autenticação...")
        run_server() # Usa a função que gerencia o loop e o shutdown interno

    def check_for_token(self, dt):
        # Recarregar .env e verificar se o token foi salvo pelo servidor FastAPI
        from dotenv import load_dotenv
        load_dotenv(envs["app_path"] + "/.env", override=True)
        
        new_token = environ.get("OAUTH_TOKEN")
        if new_token and new_token != self.oauth_token:
            logging.info("Novo token detectado no .env!")
            self.oauth_token = new_token
            self.refresh_token = environ.get("REFRESH_TOKEN")
            self.user_id = environ.get("USER_ID")
            
            self.dialog_auth.dismiss()
            self.refresh_streams_on()
            
            # Encerrar o servidor de autenticação
            UrlRequest(f"{base_auth_url}/shutdown")
            
            return False # Para o Clock.schedule_interval
        return True

    def authenticate(self, instance, *args):
        logging.info("Iniciando autenticação.")
        logging.debug(f"Instância: {instance}, Argumentos: {args}")
        if self.mod == "test":
            logging.info("Modo de teste ativado. Atualizando streams.")
            self.refresh_streams_on()
            self.dialog_auth.dismiss()
        elif args and args[0].get("error") == "Unauthorized":
            logging.warning("Token não autorizado. Tentando atualizar o token.")
            UrlRequest(
                url=f"{base_auth_url}/refresh?refresh_token={self.refresh_token}",
                on_success=lambda req, result: self.save_token(instance=req, data=result),
                on_failure=lambda req, result: logging.error("Falha ao atualizar o token.")
            )
        else:
            logging.info("Salvando novo token.")
            (
                field_token,
                field_refresh_token,
                field_user_id
            ) = self.dialog_auth.ids.content_container.children[0].children[0].ids.token.text.split(".")
            self.save_token(
                data={
                    "access_token": field_token,
                    "refresh_token": field_refresh_token,
                    "user_id": field_user_id
                }
            )
            self.dialog_auth.dismiss()

    def save_token(self, *, instance=None, data):
        logging.info("Salvando token.")
        logging.debug(f"Dados recebidos: {data}")
        if isinstance(data, str):
            response = loads(data)
        else:
            response = data

        if "message" in response and response["message"] == "Invalid refresh token":
            logging.error("Token de atualização inválido. Reabrindo diálogo de autenticação.")
            return self.dialog_authenticate()

        set_token(
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
            user_id=response["user_id"]
        )
        self.oauth_token = response["access_token"]
        self.refresh_token = response["refresh_token"]
        self.user_id = response["user_id"]

        logging.info("Token salvo com sucesso. Atualizando streams.")
        self.refresh_streams_on()

    def bottomtop(self, *args):
        if (self.scrollview_streams.vbar[0]) > (
            1 - (self.scrollview_streams.vbar[0] + self.scrollview_streams.vbar[1])
        ):
            self.scrollview_streams.scroll_y = 0
        else:
            self.scrollview_streams.scroll_y = 1

    def refresh_streams_on(self):
        logging.info("Atualizando lista de streams.")
        self.list_streams_on.clear()
        self.popup.open()
        if self.mod == "test":
            logging.info("Modo de teste ativado. Usando lista de streams fake.")
            self.list_streams_on.extend(fake_list_streams)
        elif self.oauth_token:
            logging.info("Solicitando streams seguidos da API do Twitch.")
            UrlRequest(
                url=f"https://api.twitch.tv/helix/streams/followed?type=live&user_id={self.user_id}",
                req_headers={
                    "Accept": "application/vnd.twitchtv.v5+json",
                    "Client-ID": self.client_id,
                    "Authorization": f"Bearer {self.oauth_token}",
                },
                on_success=lambda *response: self.list_streams_on.extend(parser(response)),
                on_failure=lambda *x: logging.error("Falha ao atualizar streams. Deslogando usuário.") or self.logout(x),
            )

    def on_list_streams_on(self, instance, value):
        logging.info("Lista de streams atualizada.")
        self.popup.dismiss()
        self.grid_streams.clear_widgets()
        logging.debug(f"Agendando carregamento escalonado de {min(len(self.list_streams_on), 30)} streams.")
        
        # Carrega os widgets com um pequeno delay entre eles para não travar a rede/CPU
        for i, stream in enumerate(self.list_streams_on[:30]):
            Clock.schedule_once(
                lambda dt, s=stream: self.grid_streams.add_widget(BoxStream(channel_data=s)),
                i * 0.05
            )

    def play(self, go: str, qlt="best"):
        # self.popup.open()
        self.go = go
        if not self.checkbox_auto.active and qlt == "best":
            logging.info("Buscando resoluções disponíveis.")
            Thread(target=self.search_resolutions, args=(go,)).start()
        else:
            logging.info(f"Iniciando reprodução do stream: {go} com qualidade: {qlt}")
            self.popup.chk_vlc = True
            self.popup.open()
            try:
                self.popup_resol.dismiss()
            except AttributeError:
                pass
            tmp = f'streamlink http://twitch.tv/{go} {qlt}'
            logging.debug(f"Comando executado: {tmp}")
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

        self.list_item_confirm = [
            MDListItem(
                MDListItemHeadlineText(
                        text=item,
                    ),
                MDListItemTrailingCheckbox(
                    group="group"
                ),
                theme_bg_color="Custom",
                md_bg_color=self.theme_cls.transparentColor
            )

            for item in list_r
        ]

        self.dialog = MDDialog(
            MDDialogHeadlineText(
                text="Escolha resolução:",
                halign="left",
            ),
            MDDialogContentContainer(
                *self.list_item_confirm,
                orientation="vertical",
            ),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="Play"),
                    style="text",
                    on_release=self.play_with_resolution,
                ),
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="text",
                ),
                spacing="8dp",
            ),
        )
        
        self.dialog.open()
        # breakpoint()

    def play_with_resolution(self, instance):
        for item in self.list_item_confirm:
            if item.children[0].children[0].active:
                self.popup.chk_vlc = True
                self.popup.open()
                self.play(go=self.go, qlt=item.children[1].children[0].children[0].text)
                self.dialog.dismiss()
                break

    def close_dialog(self, instance):
        self.dialog.dismiss()
