from talon import actions, cron, scope, ui, app, Module
from .poller import Poller

# Polls the current focused applications to show an indicator of where it is
class FocusPoller(Poller):
    content = None
    move_indicator_job = None
    previous_window_x = 0
    previous_window_y = 0

    def enable(self):
       if not self.enabled:
            self.enabled = True
            self.update_focus_indicator()
            ui.register("win_focus", self.update_focus_indicator)
            ui.register("win_resize", self.update_focus_indicator)
            ui.register("win_move", self.move_focus_indicator)
    
    def disable(self):
        if self.enabled:
            self.enabled = False
            ui.unregister("win_focus", self.update_focus_indicator)
            ui.unregister("win_resize", self.update_focus_indicator)
            ui.unregister("win_move", self.move_focus_indicator)        
            self.content.publish_event("screen_regions", "overlay", "remove")
        cron.cancel(self.move_indicator_job)
        
    def update_focus_indicator(self, window = None):
        if not window or window.rect.width * window.rect.height > 0:
            active_window = ui.active_window()
            if active_window:
                app = ui.active_app()
                theme = actions.user.hud_get_theme()
                focus_colour = theme.get_colour("focus_indicator_background", "DD4500")
                focus_text_colour = theme.get_colour("focus_indicator_text_colour", "FFFFFF")
                
                self.previous_window_x = active_window.rect.x
                self.previous_window_y = active_window.rect.y                
                regions = [self.content.create_screen_region("focus", focus_colour, "", "<*" + app.name, -1, active_window.rect.x, active_window.rect.y, active_window.rect.width, active_window.rect.height )]
                regions[0].text_colour = focus_text_colour
                regions[0].vertical_centered = False
                self.content.publish_event("screen_regions", "overlay", "replace", regions, True)

    def move_focus_indicator(self, window):
        cron.cancel(self.move_indicator_job)
        
        active_window = ui.active_window()
        if active_window.rect.x != self.previous_window_x and active_window.rect.y != self.previous_window_y:
            self.move_indicator_job = cron.after("30ms", self.update_focus_indicator)
        
def append_poller():
    actions.user.hud_add_poller("focus", FocusPoller())
app.register("ready", append_poller)

mod = Module()
@mod.action_class
class Actions:

    def hud_add_focus_indicator():
        """Start debugging the focus state in the Talon HUD"""
        actions.user.hud_add_poller("focus", FocusPoller())
        actions.user.hud_activate_poller("focus")
        
    def hud_remove_focus_indicator():
        """Stop debugging the focus state in the Talon HUD"""
        actions.user.hud_deactivate_poller("focus")
        actions.user.hud_clear_screen_regions("overlay", "focus")
