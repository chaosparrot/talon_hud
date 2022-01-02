from talon import scope, cron, app, actions, Module, Context
import winsound
import os
import time
import webbrowser
from user.talon_hud.display import hud

mode = "sleep"

def check_mode_changed():
    global mode
    if "command" in scope.get("mode"):
        if mode not in scope.get("mode"):
            mode = "command"    
            path = os.path.dirname(os.path.realpath(__file__))
            flags = winsound.SND_FILENAME + winsound.SND_NODEFAULT + winsound.SND_ASYNC
            winsound.PlaySound(os.path.join(path, "command_mode.wav"), flags)
    else:
        mode = "sleep"
    
def ready_thing():
    cron.interval("500ms", check_mode_changed)

app.register("ready", ready_thing)

ctx_narrator = Context()
ctx_narrator.matches = """
tag: browser
and title: /| Talon HUD narrator/
"""

mod = Module()
@mod.action_class
class Actions:
    
    def hud_focus_narrator():
        """Open a browser to open the screen readable interface"""
        webbrowser.open("file://" + os.path.join(os.path.dirname(os.path.realpath(__file__)), "index.html"))
        
# Specific HUD voice commands when the user is in the narrator context
@ctx_narrator.action_class("user")
class NarratorActions:
        
    def enable_hud_id(id: str):
        """Enables a specific HUD element"""
        global hud
        hud.enable_id(id)
        narrator_url = "file://" + os.path.join(os.path.dirname(os.path.realpath(__file__)), "index.html") + "#" + id
        actions.browser.focus_address()
        time.sleep(0.1)
        actions.insert(narrator_url)
        actions.key("enter")
        actions.key("tab")