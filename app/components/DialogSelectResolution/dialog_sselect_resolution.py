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
        self.list_item_confirm = [
            MDListItem(
                MDListItemHeadlineText(
                    text=item,
                ),
                MDListItemTrailingCheckbox(
                    group="group",
                    # Pre-select the first item for convenience
                    active=True if i == 0 else False
                ),
                theme_bg_color="Custom",
                md_bg_color=[0, 0, 0, 0],
                ripple_effect=True,
            )
            for i, item in enumerate(list_r)
        ]

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
        for item in self.list_item_confirm:
            # MDListItem children[0] is typically the Trailing Container
            # MDListItemTrailingCheckbox is usually the first child of that container
            if item.children[0].children[0].active:
                # MDListItemHeadlineText is item.children[1] or similar depending on internals
                # Safer way is to access by IDs if they were set, but here we can use the text
                return item.children[1].children[0].text
        return "best"
