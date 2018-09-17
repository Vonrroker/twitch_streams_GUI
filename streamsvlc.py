from pprint import pprint

from kivy.config import Config

Config.set('graphics', 'window_state', 'maximized')
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner

from kivy.graphics.vertex_instructions import Line
from kivy.uix.label import Label
from kivy.app import App
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.uix.boxlayout import BoxLayout
from twitch import TwitchClient
from os import system
from subprocess import Popen, check_output
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.graphics import Color, Ellipse, Rectangle
from streamlink import streams
from kivy.core.window import Window

token = open(r'C:\Users\Dayham\PycharmProjects\TwitchStreams\token.txt', 'r')
client = TwitchClient(oauth_token=token.readlines()[0])


class BoxMain(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progress_bar = ProgressBar(max=50)
        self.progress_bar.value = 1
        self.popup = Popup(title='Abrindo VLC',
                           size_hint=(None, None),
                           size=(600, 70),
                           content=self.progress_bar,
                           separator_height=0,
                           title_align='center',
                           auto_dismiss=False)
        self.popup.bind(on_open=self.puopen)

        self.hand_area = [[self.ids.btn_atualizar.size, self.ids.btn_atualizar.pos],
                          [self.ids.dwup.size, self.ids.dwup.pos],
                          [self.ids.chkauto.size, self.ids.chkauto.pos]]
        self.atualizar()
        Window.bind(mouse_pos=self.set_cursor)
        Window.bind(on_key_down=self.move)

    def move(self, *args):
        if args[1] == 274 and self.ids.scr.scroll_y > 0:
            self.ids.scr.scroll_y = self.ids.scr.scroll_y - 0.05
        elif args[1] == 273 and self.ids.scr.scroll_y < 1:
            self.ids.scr.scroll_y = self.ids.scr.scroll_y + 0.05

        # down = 274
        # up = 273

    def set_cursor(self, *args):
        pos_x = args[1][0]
        pos_y = args[1][1]
        is_area = [self.hand_area[i][1][0] < pos_x < self.hand_area[i][0][0] + self.hand_area[i][1][0] and
                   self.hand_area[i][0][1] + self.hand_area[i][1][1] > pos_y > self.hand_area[i][1][1]
                   for i in range(len(self.hand_area))]
        if any(is_area):
            Window.set_system_cursor('hand')
        else:
            Window.set_system_cursor('arrow')

    def atualizar(self):
        """
    Carrega na tela a imagem preview, Nome, nº de viewers e jogo de todos as streams ao vivo
    que você segue.
        """
        self.streams_on = [
            [x['channel']['name'], x['game'], x['viewers'], x['channel']['status'], x['preview']['large']]
            for x in client.streams.get_followed()
        ]
        self.ids.img1.clear_widgets()
        self.ids.img2.clear_widgets()
        for stream in self.streams_on:
            if self.streams_on.index(stream) % 2 == 0:
                self.ids.img1.add_widget(BoxImg(text=stream))
            else:
                self.ids.img2.add_widget(BoxImg(text=stream))

        if len(self.ids['img1'].children) > len(self.ids['img2'].children):
            self.ids.img2.add_widget(BoxLayout(size_hint_y=None, height=380))

    def play(self, go: str, qlt='best'):
        system('cls')
        self.vlcs = check_output('tasklist /nh /fi "IMAGENAME eq vlc.exe" /fo csv').count(b'vlc.exe')

        if not self.ids.chkauto.active and qlt == 'best':
            print('entrou')
            resol = (streams(f"https://www.twitch.tv/{go}")).keys()
            box_popup = BoxLayout(orientation='vertical')
            spn = Spinner(text='160p', values=list(resol)[:-2], size_hint_y=None, height=30)
            box_popup.add_widget(spn)
            box_popup.add_widget(
                Button(text='ok', size_hint_y=None, height=30, on_release=lambda a: self.play(go, spn.text)))
            self.popup_resol = Popup(title='Qualidade',
                                     size_hint=(None, None),
                                     size=(350, 600),
                                     content=box_popup,
                                     separator_height=0,
                                     title_align='center',
                                     auto_dismiss=False)
            self.popup_resol.open()
        else:
            try:
                self.popup_resol.dismiss()
            except Exception:
                pass
            self.popup.open()
            tmp = f"streamlink http://twitch.tv/{go} {qlt}"
            print(tmp)
            Popen(tmp, close_fds=True)

    def next(self, dt):
        if check_output('tasklist /nh /fi "IMAGENAME eq vlc.exe" /fo csv').count(b'vlc.exe') != self.vlcs:
            self.popup.dismiss()
            return False
        self.progress_bar.value += 1
        if self.progress_bar.value >= 50:
            self.progress_bar.value = 0

    def puopen(self, instance):
        Clock.schedule_interval(self.next, .06)


class BtnImagem(ButtonBehavior, AsyncImage):
    def __init__(self, **kwargs):
        super(BtnImagem, self).__init__(**kwargs)

    def on_press(self):
        self.color = [.4, .4, .4, 1]

    def on_release(self):
        self.color = [1, 1, 1, 1]


class BoxImg(BoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.t = text
        self.ids.asimg.source = text[4]
        self.ids.lbl.text = "{} - {} - {:,}[ref={}][color=ff0000]...[/color][/ref]".format(text[0].capitalize(),
                                                                                           text[1],
                                                                                           text[2],
                                                                                           text[0]).replace(',', '.')

    def info(self):
        if self.t[3] in self.ids.lbl.text:
            self.ids.lbl.text = self.ids.lbl.text.replace(self.t[3], '').replace('\n\n', '')
        else:
            self.ids.lbl.text += f'\n\n [color=ffc125]{self.t[3]}[/color]'


class Botao(ButtonBehavior, Label):
    cor = ListProperty([0.1, 0.5, 0.7, 1])
    cor2 = ListProperty([0.1, 0.5, 0.7, 1])

    def __init__(self, **kwargs):
        super(Botao, self).__init__(**kwargs)
        self.load()

    def on_pos(self, *args):
        self.load()

    def on_size(self, *args):
        self.load()

    def on_cor(self, *args):
        self.load()

    def on_press(self, *args):
        self.cor, self.cor2 = self.cor2, self.cor

    def on_release(self, *args):
        self.cor, self.cor2 = self.cor2, self.cor

    def load(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=self.cor)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 10, 100), width=1.4)
            # Line(points=(self.x, self.y, self.x, self.y + self.height,
            #              self.x + self.width, self.y+self.height, self.x + self.width, self.y, self.x, self.y),
            #      cap='none', joint='round', close=True, width=2)
            # Ellipse(size=(self.height, self.height),
            #         pos=self.pos)
            # Ellipse(size=(self.height, self.height),
            #         pos=(self.x + self.width - self.height, self.y))
            # Rectangle(size=(self.width - self.height, self.height),
            #           pos=(self.x + self.height / 2.0, self.y))


class Layout(App):
    title = 'Streams no VLC'

    def build(self):
        return BoxMain()


if __name__ == '__main__':
    Layout().run()

