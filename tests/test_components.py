import pytest
import webbrowser
from types import SimpleNamespace
from kivy.app import App as KivyApp
from kivy.uix.label import Label
from kivymd.app import MDApp
from kivymd.theming import ThemeManager

from app.components.BoxStream.box_stream import BoxStream
from app.components.PopUpAuth.pop_up_auth import PopUpAuth
from app.components.PopUpProgress.pop_up_progress import PopUpProgress
from app.components.DialogSelectResolution.dialog_sselect_resolution import DialogSelectResolution
import app.components.DialogSelectResolution.dialog_sselect_resolution as dialog_module


class DummyMDApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls = ThemeManager()


@pytest.fixture(autouse=True)
def md_app():
    previous_app = KivyApp._running_app
    app = DummyMDApp()
    KivyApp._running_app = app
    yield app
    KivyApp._running_app = previous_app


def _find_button(widget, text):
    if getattr(widget, "text", None) == text:
        return widget
    for child in getattr(widget, "children", []):
        found = _find_button(child, text)
        if found:
            return found
    return None


def test_boxstream_initializes_properties_and_formats_viewers(monkeypatch):
    monkeypatch.setattr("kivy.animation.Animation.start", lambda self, widget: None)

    channel_data = {
        "channel_status": "live",
        "channel_name": "testchan",
        "preview_img": "http://example.com/image.png",
        "game": "Test Game",
        "viewers": 1234,
    }

    box = BoxStream(channel_data)
    assert box.status == "live"
    assert box.stream == "testchan"
    assert box.preview_img == "http://example.com/image.png"
    assert box.channel_name == "Testchan"
    assert box.game == "Test Game"
    assert box.viewers_count == "1.234"

    label = Label(opacity=0, text="")
    box.ids = {"label_status": label}
    box.info()
    assert label.text == "live"

    label.opacity = 1
    box.info()
    assert label.text == "live"


def test_popupauth_builds_dialog_and_opens_browser(monkeypatch):
    open_calls = []

    def fake_open(url):
        open_calls.append(url)

    monkeypatch.setattr(webbrowser, "open", fake_open)

    button_callback = {}
    original_button_init = getattr(__import__("kivymd.uix.button.button", fromlist=["MDButton"]), "MDButton").__init__

    def patched_button_init(self, *args, **kwargs):
        button_callback["on_release"] = kwargs.get("on_release")
        original_button_init(self, *args, **kwargs)

    monkeypatch.setattr("kivymd.uix.button.button.MDButton.__init__", patched_button_init)

    popup = PopUpAuth(authenticate=lambda *args: None, base_auth_url="http://localhost:5000")
    assert popup.auto_dismiss is False
    assert button_callback.get("on_release") is not None

    button_callback["on_release"](None)
    assert open_calls == ["http://localhost:5000/auth/twitch"]


def test_popupprogress_on_open_detects_vlc_change_and_closes(monkeypatch):
    monkeypatch.setattr("app.components.PopUpProgress.pop_up_progress.process_iter", lambda attrs: [])
    popup = PopUpProgress(chk_vlc=True)
    assert popup.chk_vlc is True

    schedule_calls = []
    monkeypatch.setattr("kivy.clock.Clock.schedule_interval", lambda callback, interval: schedule_calls.append((callback, interval)))
    monkeypatch.setattr("kivy.clock.Clock.unschedule", lambda callback: None)
    monkeypatch.setattr(
        "app.components.PopUpProgress.pop_up_progress.process_iter",
        lambda attrs: [SimpleNamespace(info={"name": "vlc.exe"})],
    )

    dismissed = []
    monkeypatch.setattr(popup, "dismiss", lambda *args, **kwargs: dismissed.append(True))

    result = popup.on_open()
    assert schedule_calls == [(popup.next, 0.5)]
    assert dismissed == [True]
    assert result is False
    assert popup.chk_vlc is False


def test_popupprogress_next_closes_dialog_when_vlc_changes(monkeypatch):
    monkeypatch.setattr("app.components.PopUpProgress.pop_up_progress.process_iter", lambda attrs: [])
    popup = PopUpProgress()
    assert popup.vlcs == 0

    dismissed = []
    monkeypatch.setattr(popup, "dismiss", lambda *args, **kwargs: dismissed.append(True))
    monkeypatch.setattr(
        "app.components.PopUpProgress.pop_up_progress.process_iter",
        lambda attrs: [SimpleNamespace(info={"name": "vlc.exe"})],
    )

    result = popup.next(0)
    assert dismissed == [True]
    assert result is False
    assert popup.chk_vlc is False


def test_dialogselectresolution_sets_title_color_when_ids_available(monkeypatch):
    original_init = dialog_module.MDDialog.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.ids = {"title": Label()}

    monkeypatch.setattr(dialog_module.MDDialog, "__init__", patched_init)

    dialog = DialogSelectResolution()
    assert dialog.ids["title"].color == [1, 1, 1, 1]
