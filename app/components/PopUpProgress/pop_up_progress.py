import logging
from kivy.clock import Clock
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from psutil import process_iter
from kivymd import images_path

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
        self.background = f'{images_path}/transparent.png'
        self.size_hint = (None, None)
        self.size = (300, 300)
        self.separator_height = 0
        self.auto_dismiss = False

        logging.info("Inicializando PopUpProgress.")
        proc = [x.info["name"].replace(".exe", "") for x in process_iter(["name"])]
        self.vlcs = proc.count("vlc")
        logging.debug(f"Processos encontrados: {proc}")
        logging.debug(f"Contagem inicial de VLC: {self.vlcs}")

        self.add_widget(MDCircularProgressIndicator(
            size_hint=(None, None),
            size=self.size
        ))

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
        logging.debug(f"Processos no next: {proc}")
        logging.debug(f"Contagem de VLC no next: {checking}")

        if checking != self.vlcs:
            logging.info("Mudança detectada na contagem de VLC. Fechando PopUpProgress.")
            self.dismiss()
            self.chk_vlc = False
            return False
