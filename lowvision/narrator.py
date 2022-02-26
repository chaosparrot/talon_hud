from talon import actions, Module, Context
import os

narrator_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "narrator")

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
        webbrowser.open("file://" + os.path.join(narrator_directory, "index.html"))
        
# Specific HUD voice commands when the user is in the narrator context
#@ctx_narrator.action_class("user")
#class NarratorActions:
#        
#    def hud_enable_id(id: str):
#        """Enables a specific HUD element"""
#        global hud
#        hud.enable_id(id)
#        narrator_url = "file://" + os.path.join(narrator_directory, "index.html") + "#" + id
#        actions.browser.focus_address()
#        time.sleep(0.1)
#        actions.insert(narrator_url)
#        actions.key("enter")
#        actions.key("tab")