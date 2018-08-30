from kivy.config import Config

Config.set('graphics', 'window_state', 'maximized')
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
        self.atualizar()

    def atualizar(self):
        """
    Carrega na tela a imagem preview, Nome, nº de viewers e jogo de todos as streams ao vivo
    que você segue.
        """
        self.streams_on = [
            [x['channel']['name'], x['game'], x['viewers'], x['channel']['status'], x['preview']['large'], 'twich']
            for x in client.streams.get_followed()
        ]
        self.ids.img1.clear_widgets()
        self.ids.img2.clear_widgets()
        for stream in self.streams_on:
            if self.streams_on.index(stream) % 2 == 0:
                self.ids.img1.add_widget(Boxlayout1(text=stream))
            else:
                self.ids.img2.add_widget(Boxlayout1(text=stream))

        if len(self.ids['img1'].children) > len(self.ids['img2'].children):
            self.ids.img2.add_widget(BoxLayout(size_hint_y=None, height=380, padding=[2, 2, 2, 2]))

    def play(self, go: str):
        # pprint(self.streams_on)

        system('cls')
        self.vlcs = check_output('tasklist /nh /fi "IMAGENAME eq vlc.exe" /fo csv').count(b'vlc.exe')
        self.popup.open()
        tmp = f"streamlink http://twitch.tv/{go} best"
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


class Boxlayout1(BoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.ids.asimg.source = text[4]
        self.ids.lbl.text = "{} - {} - {:,}".format(text[0].capitalize(), text[1], text[2]).replace(',', '.')


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
            Ellipse(size=(self.height, self.height),
                    pos=self.pos)
            Ellipse(size=(self.height, self.height),
                    pos=(self.x + self.width - self.height, self.y))
            Rectangle(size=(self.width - self.height, self.height),
                      pos=(self.x + self.height / 2.0, self.y))


class Layout(App):
    title = 'Streams no VLC'

    def build(self):
        return BoxMain()


if __name__ == '__main__':
    Layout().run()
