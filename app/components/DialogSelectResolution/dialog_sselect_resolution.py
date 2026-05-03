from kivy.uix.widget import Widget
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
)
from kivymd.uix.list import (
    MDListItem,
    MDListItemHeadlineText,
    MDListItemTrailingCheckbox,
)


class DialogSelectResolution(MDDialog):
    def __init__(self, list_r, play_callback, **kwargs):
        self.items_data = []
        self.list_item_confirm = []
        
        for i, item in enumerate(list_r):
            checkbox = MDListItemTrailingCheckbox(
                group="group",
                # Pre-select the first item for convenience
                active=True if i == 0 else False
            )
            
            list_item = MDListItem(
                MDListItemHeadlineText(
                    text=item,
                ),
                checkbox,
                theme_bg_color="Custom",
                md_bg_color=[0, 0, 0, 0],
                ripple_effect=True,
            )
            
            self.items_data.append({"resolution": item, "checkbox": checkbox})
            self.list_item_confirm.append(list_item)

        super().__init__(
            MDDialogHeadlineText(
                text="Select Resolution",
                halign="left",
            ),
            MDDialogContentContainer(
                *self.list_item_confirm,
                orientation="vertical",
            ),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="text",
                    on_release=self.dismiss,
                ),
                MDButton(
                    MDButtonText(text="Play"),
                    style="filled",
                    on_release=lambda x: play_callback(self.get_selected_resolution()),
                ),
                spacing="8dp",
            ),
            **kwargs
        )

    def get_selected_resolution(self):
        for data in self.items_data:
            if data["checkbox"].active:
                return data["resolution"]
        return "best"
