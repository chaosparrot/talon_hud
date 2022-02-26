from typing import Dict
from talon.scripting import Dispatch

# Class for general communication between the different layers of the HUD
# NOTE - THIS USES A TALON API THAT IS SUBJECT TO CHANGE AND MIGHT BREAK IN FUTURE VERSIONS
class HeadUpEventDispatch(Dispatch):

    def request_persist_preferences(self):
        self.dispatch("persist_preferences", True)
        
    def hide_context_menu(self):
        self.dispatch("hide_context_menu", True)
        
    def show_context_menu(self, widget_id, position = None, buttons = None):
        self.dispatch("show_context_menu", widget_id, position, buttons)
        
    def deactivate_poller(self, poller_name):
        self.dispatch("deactivate_poller", poller_name)
        
    def synchronize_widget_poller(self, widget_id):
        self.dispatch("synchronize_poller", widget_id)