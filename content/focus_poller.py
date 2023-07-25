from talon import actions, cron, scope, ui, app, Module
from .poller import Poller

# Polls the current focused applications to show an indicator of where it is
class FocusPoller():
    callbacks = {}
    move_indicator_job = None
    previous_window_x = None
    previous_window_y = None
    
    def register(self, name, callback):
        current_callback_amount = len(self.callbacks.values())
        self.callbacks[name] = callback
        if (current_callback_amount == 1):
            ui.register("win_focus", self.update_focus)
            ui.register("win_resize", self.update_focus)
            ui.register("win_move", self.move_focus)
            self.move_indicator_job = cron.after("100ms", self.update_focus)
            print( "ENABLING FOCUS TRACKING!" )
    
    def unregister(self, name):
        if name in self.callbacks:
            del self.callbacks[name]
        
        self.previous_mode = None
        current_callback_amount = len(self.callbacks.values())
        if (current_callback_amount <= 1):
            ui.unregister("win_focus", self.update_focus)
            ui.unregister("win_resize", self.update_focus)
            ui.unregister("win_move", self.move_focus)
            cron.cancel(self.move_indicator_job)
            print( "DISABLING FOCUS TRACKING!" )            

    def update_focus(self, window = None):
        if not window or window.rect.width * window.rect.height > 0:
            active_window = ui.active_window()
            if active_window:
                app = ui.active_app()
                self.previous_window_x = active_window.rect.x
                self.previous_window_y = active_window.rect.y
                
                callbacks = list(self.callbacks.values())[:]
                for callback in callbacks:
                    callback(active_window, app)
    
    def move_focus(self, window):
        cron.cancel(self.move_indicator_job)
        
        active_window = ui.active_window()
        if active_window.rect.x != self.previous_window_x and active_window.rect.y != self.previous_window_y:
            self.move_indicator_job = cron.after("30ms", self.update_focus)

class PartialFocusPoller(Poller):
    content = None
    enabled = False
    poller: FocusPoller

    def __init__(self, type, poller: FocusPoller):
        self.type = type
        self.poller = poller
    
    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.poller.register(self.type, self.update_focus)

    def disable(self):
        if self.enabled:
            self.enabled = False
            self.poller.unregister(self.type)
            self.content.publish_event("status_icons", self.type, "remove")
            self.content.publish_event("screen_regions", "focus", "remove")

    def update_focus(self, window, app):
        if self.type == "focus_toggle" and window is not None and app is not None and self.content is not None:
            theme = actions.user.hud_get_theme()
            focus_colour = theme.get_colour("focus_indicator_background", "DD4500")
            focus_text_colour = theme.get_colour("focus_indicator_text_colour", "FFFFFF")
            
            regions = [self.content.create_screen_region("focus", focus_colour, "", "<*" + app.name, -1, window.rect.x, window.rect.y, window.rect.width, window.rect.height )]
            regions[0].text_colour = focus_text_colour
            regions[0].vertical_centered = False
            self.content.publish_event("screen_regions", "focus", "replace", regions)

            status_icon = self.content.create_status_icon("focus_toggle", "focus", None, app.name, lambda _, _2: actions.user.hud_deactivate_poller("focus_toggle") )
            self.content.publish_event("status_icons", status_icon.topic, "replace", status_icon)

    def destroy(self):
        super().destroy()
        self.poller = None


focus_poller = FocusPoller()
def add_focus_toggle():
    actions.user.hud_activate_poller("focus_toggle")

def remove_focus_toggle():
    actions.user.hud_deactivate_poller("focus_toggle")
    actions.user.hud_remove_status_icon("focus_toggle")

def on_ready():
    actions.user.hud_add_poller("focus", PartialFocusPoller("focus", focus_poller), True)
    actions.user.hud_add_poller("focus_toggle", PartialFocusPoller("focus_toggle", focus_poller))

    default_option = actions.user.hud_create_button("Add focus indicator", lambda _: add_focus_toggle(), "focus")
    activated_option = actions.user.hud_create_button("Remove focus indicator", lambda _: remove_focus_toggle(), "focus")
    status_option = actions.user.hud_create_status_option("focus_toggle", default_option, activated_option)
    actions.user.hud_publish_status_option("focus_toggle_option", status_option)
    
app.register("ready", on_ready)

mod = Module()
@mod.action_class
class Actions:

    def hud_activate_focus_indicator(): 
        """Activate the focus indicator"""
        actions.user.hud_activate_poller("focus_toggle")
        
    def hud_deactivate_focus_indicator():
        """Deactivate the focus indicator"""
        actions.user.hud_deactivate_poller("focus_toggle")