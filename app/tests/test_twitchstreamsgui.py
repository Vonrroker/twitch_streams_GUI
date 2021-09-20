import unittest
from contextlib import contextmanager
from time import sleep
from kivy import lang
from kivy.lang import Builder
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.tests.common import GraphicUnitTest, UnitTestTouch

from config import envs
from main import MyApp


app_path = envs["app_path"]


def touch(btn):
    t = UnitTestTouch(*btn)
    t.touch_down()

    t.touch_up()


@contextmanager
def window_loop():
    EventLoop.ensure_window()
    yield EventLoop.window.children[0]


class TestMainBox(GraphicUnitTest):
    app = MyApp()
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
        # self.render(self.box)
        assert self.box.scrollview_streams.scroll_y == 1
        touch(self.box.button_bottomtop.center)
        assert self.box.scrollview_streams.scroll_y == 0
        touch(self.box.button_bottomtop.center)
        assert self.box.scrollview_streams.scroll_y == 1

    def test_label_channel_infos_deve_mostrar_titulo_da_live(self):
        assert (
            self.box.grid_streams.children[0].label_channel_infos.text
            == "Name_20 - Nome do Jogo_20 - 0"
        )

    def test_press_icondownarrow_boximg_deve_mostrar_status_da_live(self):
        with window_loop() as window:

            assert window.children[0].children[0].children[-1].label_status.text == ""

            self.box.grid_streams.children[
                -1
            ].button_show_status.on_press = self.box.grid_streams.children[-1].info(
                self.box.grid_streams.children[-1]
            )

            touch(self.box.grid_streams.children[-1].button_show_status.center)

            assert (
                window.children[0].children[0].children[-1].label_status.text
                == "It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. "
            )


# class GridLayoutTest(unittest.TestCase):
#     def test_gridlayout_get_max_widgets_with_3cols_rows(self):
#         app = MyApp()

#         app.kv_directory = f"{app_path}"
#         app.kv_file = "app.kv"
#         app.mod = "testing"
#         app.load_kv()

#         box = app.build()
#         gl = box.grid_streams
#         gl.rows = 5
#         expected = 15
#         value = gl.get_max_widgets()
#         self.assertEqual(expected, value)


# class BoxStreamTest(GraphicUnitTest):
#     def test_press_icondownarrow_boximg_deve_mostrar_status_da_live(self):
#         from boxmain import BoxStream
#         from kivymd.app import MDApp
#         from fakes.list_streams import fake_list_streams

#         print(app_path)
#         app = MDApp()

#         box = app.build()
#         box.add_widget(BoxStream(channel_data=fake_list_streams[0]))
#         self.render(box)

#         assert box.children[0].label_status.text == ""

#         touch(box.children[0].button_show_status.center)

#         assert (
#             box.children[0].label_status.text
#             == "It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. "
#         )
