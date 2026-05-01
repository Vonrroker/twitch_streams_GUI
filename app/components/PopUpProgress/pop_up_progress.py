import logging
from kivy.clock import Clock
from psutil import process_iter

from kivymd.uix.dialog import MDDialog, MDDialogContentContainer
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.boxlayout import MDBoxLayout

# Configuração básica do logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

class PopUpProgress(MDDialog):
    def __init__(self, chk_vlc=False, **kwargs):
        super().__init__(**kwargs)
        self.chk_vlc = chk_vlc
        self.auto_dismiss = False
        
        # Tenta definir transparência após o super().__init__
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0]
        self.shadow_color = [0, 0, 0, 0]

        logging.info("Inicializando PopUpProgress.")
        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        self.vlcs = proc.count("vlc")
        logging.debug(f"Contagem inicial de VLC: {self.vlcs}")

        content = MDBoxLayout(
            MDCircularProgressIndicator(
                size_hint=(None, None),
                size=("48dp", "48dp"),
                pos_hint={"center_x": .5, "center_y": .5}
            ),
            orientation="vertical",
            adaptive_height=True,
            padding="24dp"
        )
        content.theme_bg_color = "Custom"
        content.md_bg_color = [0, 0, 0, 0]

        container = MDDialogContentContainer()
        container.add_widget(content)

        self.add_widget(container)

    def on_open(self):
        logging.info("PopUpProgress aberto.")
        if self.chk_vlc:
            logging.info("Monitoramento de VLC ativado.")
            Clock.schedule_interval(self.next, 0.5)
        else:
            logging.info("Monitoramento de VLC desativado.")
            Clock.unschedule(self.next)

        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")
        logging.debug(f"Contagem de VLC no on_open: {checking}")

        if checking != self.vlcs:
            logging.info("Mudança detectada na contagem de VLC. Fechando PopUpProgress.")
            self.dismiss()
            self.chk_vlc = False
            return False
    

    def next(self, dt):
        logging.info("Executando verificação periódica de processos.")
        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        checking = proc.count("vlc")
        # logging.debug(f"Processos no next: {proc}")
        logging.debug(f"Contagem de VLC no next: {checking}")

        if checking != self.vlcs:
            logging.info("Mudança detectada na contagem de VLC. Fechando PopUpProgress.")
            self.dismiss()
            self.chk_vlc = False
            return False
