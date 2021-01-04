import unittest
from contextlib import contextmanager

from kivy import lang
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.tests.common import GraphicUnitTest, UnitTestTouch

from config import envs
from main import App


app_path = envs["app_path"]


@contextmanager
def touch(btn):
    t = UnitTestTouch(*btn)
    t.touch_down()
    yield
    t.touch_up()


@contextmanager
def window_loop():
    EventLoop.ensure_window()
    yield EventLoop.window.children[0]


class TestMainBox(GraphicUnitTest):
    app = App()

    app.kv_directory = f"{app_path}"
    app.kv_file = "app.kv"
    app.mod = "testing"

    app.load_kv()

    box = app.build()

    def test_start_raw_app(self):
        lang._delayed_start = None
        Clock.schedule_once(self.app.stop, 0.1)
        self.app.run()

    def test_criacao_componentes_iniciais(self):
        self.render(self.box)
        with window_loop() as window:
            assert window.children[0] == self.box.scrollview_streams
            assert window.children[0].children[0] == self.box.grid_streams
            assert (
                window.children[0].children[0].children[0]
                == self.box.grid_streams.children[0]
            )
            assert window.children[1].children[1].children[0] == self.box.checkbox_auto
            assert window.children[1].children[0] == self.box.button_bottomtop
            assert window.children[1].children[2] == self.box.button_refresh

    def test_press_downup_deve_rolar_tela_a_extremo_oposto(self):
        assert self.box.scrollview_streams.scroll_y == 1
        with touch(self.box.button_bottomtop.center):
            assert self.box.scrollview_streams.scroll_y == 0
        with touch(self.box.button_bottomtop.center):
            assert self.box.scrollview_streams.scroll_y == 1

    def test_press_icondownarrow_boximg_deve_mostrar_titulo_da_live(self):
        assert (
            self.box.grid_streams.children[0].label_channel_infos.text
            == "Name_20 - Nome do Jogo_20 - 0"
        )

        assert self.box.grid_streams.children[0].label_status.text == ""


class GridLayoutTest(unittest.TestCase):
    def test_gridlayout_get_max_widgets_with_3cols_rows(self):
        app = App()

        app.kv_directory = f"{app_path}"
        app.kv_file = "app.kv"
        app.mod = "testing"
        app.load_kv()

        box = app.build()
        gl = box.grid_streams
        gl.rows = 5
        expected = 15
        value = gl.get_max_widgets()
        self.assertEqual(expected, value)
