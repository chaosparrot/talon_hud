from talon import actions, cron, scope, ui, app, Module
from .poller import Poller
from .state import hud_content
from .typing import HudStatusIcon, HudButton, HudStatusOption

# Polls the current mode state to be displayed in widgets like the status bar
class ModePoller():
    previous_mode = None
    job = None
    callbacks = {}
    
    def register(self, name, callback):
        current_callback_amount = len(self.callbacks.values())
        self.callbacks[name] = callback
        if (current_callback_amount == 0):
            self.job = cron.interval("200ms", self.state_check)

    def unregister(self, name):
        if name in self.callbacks:
            del self.callbacks[name]
        
        self.previous_mode = None
        current_callback_amount = len(self.callbacks.values())
        if (current_callback_amount == 0):
            cron.cancel(self.job)
            self.job = None

    def state_check(self):
        current_mode = actions.user.hud_determine_mode()
        if current_mode != self.previous_mode:
            self.previous_mode = current_mode
        
            callbacks = list(self.callbacks.values())[:]
            for callback in callbacks:
                callback(current_mode)

class PartialModePoller(Poller):
    content = None
    enabled = False
    poller: ModePoller

    def __init__(self, type, poller: ModePoller):
        self.type = type
        self.poller = poller
    
    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.poller.register(self.type, self.update_mode)
            if self.type == "mode_toggle" and self.poller.previous_mode is not None:
                self.publish_statusbar_icon(self.poller.previous_mode)

    def disable(self):
        if self.enabled:
            self.enabled = False
            self.poller.unregister(self.type)
            if self.type == "mode_toggle":
                self.content.publish_event("status_icons", "mode_toggle", "remove")

    def update_mode(self, current_mode):
        if self.type == "mode_toggle":
            self.publish_statusbar_icon(current_mode)
        elif self.type == "mode":
            self.content.publish_event("variable", "mode", "replace", current_mode)

    def publish_statusbar_icon(self, current_mode):
        status_icon = self.content.create_status_icon("mode_toggle", current_mode + "_icon", None, current_mode + " mode", lambda _, _2: actions.user.hud_toggle_mode())
        self.content.publish_event("status_icons", status_icon.topic, "replace", status_icon)

    def destroy(self):
        super().destroy()
        self.poller = None


mode_poller = ModePoller()
def add_mode_toggle():
    actions.user.hud_activate_poller("mode_toggle")

def remove_mode_toggle():
    actions.user.hud_deactivate_poller("mode_toggle")
    actions.user.hud_remove_status_icon("mode_toggle")

def on_ready():
    actions.user.hud_add_poller("mode", PartialModePoller("mode", mode_poller), True) # This poller needs to be kept alive so that the sleep state is properly sent to all widgets
    actions.user.hud_add_poller("mode_toggle", PartialModePoller("mode_toggle", mode_poller))

    add_mode_option = HudButton("command_icon", "Add mode indicator", ui.Rect(0,0,0,0), lambda widget: add_mode_toggle())
    remove_mode_option = HudButton("command_icon", "Remove mode indicator", ui.Rect(0,0,0,0), lambda widget: remove_mode_toggle())
    mode_option = HudStatusOption("mode_toggle", add_mode_option, remove_mode_option)
    actions.user.hud_publish_status_option("mode_option", mode_option)
    
app.register("ready", on_ready)

mod = Module()
@mod.action_class
class Actions:

    def hud_get_status_modes() -> list[str]:
        """Get an ordered list of all the available modes that can be displayed in the status bar and other widget states"""
        return ["dictation", "command", "sleep"]

    def hud_determine_mode() -> str:
        """Determine the current mode used for the status bar icons and the widget states"""
        active_modes = scope.get("mode")
        available_modes = actions.user.hud_get_status_modes()
        
        current_mode = "command"
        for available_mode in available_modes:
            if available_mode in active_modes:
                current_mode = available_mode
                break
        
        return current_mode

    def hud_toggle_mode():
        """Toggle the current mode to a new mode"""
        current_mode = actions.user.hud_determine_mode()
        if current_mode in ["command", "dictation"]:
             actions.speech.disable()
        elif current_mode == "sleep":
             actions.speech.enable()
        
        
