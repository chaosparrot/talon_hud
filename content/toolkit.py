from talon import actions, cron, scope, speech_system, ui, app, Module
from user.talon_hud.content.state import hud_content

def pick_toolkit_option(data):
    if data["text"] == "Debugging":
        actions.user.hud_toolkit_debug_options()
        return True
    elif data["text"] == "Scope":
        actions.user.hud_toolkit_scope()
        return False        
    elif data["text"] == "Speech":
        actions.user.hud_toolkit_speech()
        return False
    elif data["text"] == "Lists":
        actions.user.hud_toolkit_lists()
        return True
    elif data["text"] == "History":
        actions.user.hud_toolkit_history()
        return False
    elif data["text"] == "Microphone selection":
        actions.user.show_microphone_options()
        return True
    elif data["text"] == "Documentation":
        actions.user.hud_show_documentation()
        return False
    elif data["text"] == "Walkthroughs":
        actions.user.hud_show_walkthroughs()
        return True

mod = Module()

@mod.action_class
class Actions:

    def hud_toolkit_options():
        """Shows the content available in the HUD toolkit"""
        choices = actions.user.hud_create_choices([
            {"text": "Documentation"},
            {"text": "Walkthroughs"},            
            {"text": "Debugging"},
            {"text": "Microphone selection"},
            {"text": "Dismiss toolkit"}
        ], pick_toolkit_option)
        actions.user.hud_publish_choices(choices, "Toolkit options", "Pick content from the HUD Toolkit below")
        
    def hud_toolkit_debug_options():
        """Shows the content available in the debug menu of the HUD toolkit"""
        choices = actions.user.hud_create_choices([
            {"text": "Scope"},
            {"text": "Lists"},
            {"text": "Speech"},
            {"text": "Dismiss toolkit"}
        ], pick_toolkit_option)
        actions.user.hud_publish_choices(choices, "Toolkit debugging", "Pick content from the HUD Toolkit below")
