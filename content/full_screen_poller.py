from talon import actions, cron, scope, app, ctrl, ui, Module
from .poller import Poller
from time import perf_counter

mod = Module()
mod.tag("talon_hud_automatic_hide", desc="A tag that, when enabled, automatically hides the HUD when it is inactive in a fullscreen application")

# About the same threshold as Youtube fading controls
inactivity_threshold = 3.5

# Checks if we are currently in a full screen application and if we should make the HUD invisible in that case
class FullScreenPoller(Poller):
    content = None
    job = None
    mouse_check_job = None
    last_mouse_pos = None
    enabled = False
    disabled_visibility = False
    last_activity = perf_counter()

    activity_count = 0
    last_content = None

    def enable(self):
       if not self.enabled:
            self.enabled = True
            cron.cancel(self.job)
            self.job = cron.interval("500ms", self.state_check)

    def disable(self):
        if self.enabled:
            self.enabled = False
            cron.cancel(self.job)
            self.job = cron.interval("500ms", self.state_check)

    def is_full_screen(self):
        active_window = ui.active_window()
        if active_window is not None:
            for screen in ui.screens():
                if round(screen.x) == round(active_window.rect.x) and \
                    round(screen.y) == round(active_window.rect.y) and \
                    round(screen.width) == round(active_window.rect.width) and \
                    round(screen.height) == round(active_window.rect.height):
                    return True

        return False

    def state_check(self):
        tags = scope.get("tag")

        if tags is not None and "user.talon_hud_automatic_hide" in tags:
            modes = scope.get("mode")
            inactive = ( modes is not None and "sleep" in modes ) or actions.sound.active_microphone() == "None"

            if inactive and self.is_full_screen():
                self.activity_count = 0
                if perf_counter() - self.last_activity > inactivity_threshold and self.disabled_visibility == False:
                    self.disabled_visibility = True
                    actions.user.hud_set_inactive_visibility(False)
                    self.mouse_check_job = cron.interval("300ms", self.check_for_mouse_change)
            else:
                self.detect_last_activity()
        else:
            self.detect_last_activity()

    def check_for_mouse_change(self):
        if self.last_mouse_pos is None:
            self.last_mouse_pos = ctrl.mouse_pos()
        elif self.last_mouse_pos != ctrl.mouse_pos():
            self.last_mouse_pos = ctrl.mouse_pos()
            self.detect_last_activity(True)
    
    def detect_last_activity(self, activity = False):
        self.last_activity = perf_counter()

        # Keep an activity count so that random pop ups or invisible windows that could happen during full screen would
        # Cause the HUD appearing again for a brief moment in time
        self.activity_count += 1
        if self.disabled_visibility and (self.activity_count > 3 or activity):
            actions.user.hud_set_inactive_visibility(True)
            self.disabled_visibility = False
            cron.cancel(self.mouse_check_job)
            self.mouse_check_job = None
            self.last_mouse_pos = None
    
    def destroy(self):
        super().destroy()
        cron.cancel(self.job)
        self.job = None
        cron.cancel(self.mouse_check_job)
        self.mouse_check_job = None
                
def append_poller():
    actions.user.hud_add_poller("inactivity_poller", FullScreenPoller(), True)
app.register("ready", append_poller)