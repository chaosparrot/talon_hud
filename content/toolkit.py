from talon import actions, cron, scope, speech_system, ui, app, Module
from user.talon_hud.content.state import hud_content

def pick_toolkit_option(data):
    if data["text"] == "Talon scope":
        actions.user.hud_toolkit_scope()
        return False
    elif data["text"] == "Microphone selection":
        actions.user.show_microphone_options()
        return True
    elif data["text"] == "Documentation":
        actions.user.hud_show_documentation()
        return False
    elif data["text"] == "Walkthroughs":
        actions.user.hud_show_walkthroughs()
        return False

mod = Module()

@mod.action_class
class Actions:

    def hud_toolkit_options():
        """Shows the content available in the HUD toolkit"""
        choices = actions.user.hud_create_choices([
            {"text": "Documentation"},
            {"text": "Walkthroughs"},            
            {"text": "Talon scope"},
            {"text": "Microphone selection"},
            {"text": "Cancel toolkit"}
        ], pick_toolkit_option)
        actions.user.hud_publish_choices(choices, "Toolkit options", "Pick content from the HUD Toolkit below")
