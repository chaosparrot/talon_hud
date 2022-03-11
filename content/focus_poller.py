from talon import actions, cron, scope, ui, app
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
            self.content.publish_event("status_icons", "focus_toggle", "remove")
            self.content.publish_event("screen_regions", "focus", "remove")
            ui.unregister("win_focus", self.update_focus_indicator)
            ui.unregister("win_resize", self.update_focus_indicator)
            ui.unregister("win_move", self.move_focus_indicator)
            cron.cancel(self.move_indicator_job)

    def update_focus_indicator(self, window = None):
        if not window or window.rect.width * window.rect.height > 0 and self.enabled:
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
                self.content.publish_event("screen_regions", "focus", "replace", regions)

                status_icon = self.content.create_status_icon("focus_toggle", "focus", None, app.name, lambda _, _2: actions.user.hud_deactivate_poller("focus") )
                self.content.publish_event("status_icons", status_icon.topic, "replace", status_icon)

    def move_focus_indicator(self, window):
        cron.cancel(self.move_indicator_job)
        
        active_window = ui.active_window()
        if active_window.rect.x != self.previous_window_x and active_window.rect.y != self.previous_window_y:
            self.move_indicator_job = cron.after("30ms", self.update_focus_indicator)
        
def append_poller():
    actions.user.hud_add_poller("focus", FocusPoller())
    
    # Add the toggles to the status bar
    default_option = actions.user.hud_create_button("Add focus indicator", lambda _: actions.user.hud_activate_poller("focus"), "focus")
    activated_option = actions.user.hud_create_button("Remove focus indicator", lambda _: actions.user.hud_deactivate_poller("focus"), "focus")
    status_option = actions.user.hud_create_status_option("focus_toggle", default_option, activated_option)
    actions.user.hud_publish_status_option("focus_toggle_option", status_option)

app.register("ready", append_poller)