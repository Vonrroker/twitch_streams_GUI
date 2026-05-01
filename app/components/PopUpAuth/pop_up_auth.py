from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogContentContainer, MDDialogButtonContainer
from kivymd.theming import ThemeManager
import webbrowser



class Content(MDBoxLayout):
    ...

class PopUpAuth(MDDialog):
    def __init__(self, authenticate, base_auth_url, **kwargs):
        super().__init__(**kwargs)
        # self.ids.title.color = self.theme_cls.primary_color
        # self.title = "Entre no link para fazer a autenticação."
        # self.type = "custom"
        # self.theme_text_color = "Primary"
        self.auto_dismiss = False
        self.aut = authenticate
        self.add_widget(
            MDDialogHeadlineText(
                text="Entre no link para fazer a autenticação.",
                halign="left",
            ),
        )
        self.add_widget(
            MDDialogContentContainer(
                Content(),
                
                orientation="vertical"
            ),
        )
        self.add_widget(
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Abrir Link no Navegador"),
                    style="text",
                    on_release=lambda arg: webbrowser.open(
                        f"{base_auth_url}/auth/twitch"
                    ),
                ),
            ),
        )

