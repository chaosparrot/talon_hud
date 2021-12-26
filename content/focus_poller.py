from talon import actions, cron, scope, ui, app, Module
from user.talon_hud.content.poller import Poller

# Polls the current focused applications to show an indicator of where it is
class FocusPoller(Poller):
    move_indicator_job = None

    def enable(self):
       if not self.enabled:
            self.enabled = True
            self.update_focus_indicator()
            ui.register('win_focus', self.update_focus_indicator)
            ui.register('win_move', self.move_focus_indicator)
    
    def disable(self):
        self.enabled = False
        ui.unregister('win_focus', self.update_focus_indicator)
        ui.unregister('win_move', self.move_focus_indicator)
        actions.user.hud_publish_screen_regions('overlay', [], True)
        cron.cancel(self.move_indicator_job)
        
    def update_focus_indicator(self, window = None):
        if not window or window.rect.width * window.rect.height > 0:
            active_window = ui.active_window()
            if active_window:
                app = ui.active_app()
                regions = [actions.user.hud_create_screen_region('focus', 'DD4500', '', '<*' + app.name, -1, active_window.rect.x, active_window.rect.y, active_window.rect.width, active_window.rect.height )]
                actions.user.hud_publish_screen_regions('overlay', regions, True)

    def move_focus_indicator(self, window):
        cron.cancel(self.move_indicator_job)
        self.move_indicator_job = cron.after("30ms", self.update_focus_indicator)
        
def append_poller():
    actions.user.hud_add_poller('focus', FocusPoller())
app.register('ready', append_poller)

mod = Module()
@mod.action_class
class Actions:

    def hud_add_focus_indicator():
        """Start debugging the focus state in the Talon HUD"""
        actions.user.hud_add_poller('focus', FocusPoller())
        actions.user.hud_activate_poller('focus')
        
    def hud_remove_focus_indicator():
        """Stop debugging the focus state in the Talon HUD"""
        actions.user.hud_deactivate_poller('focus')
        actions.user.hud_clear_screen_regions('overlay', 'focus')
