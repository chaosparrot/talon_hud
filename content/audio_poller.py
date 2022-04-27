from talon import actions, cron, app
from .poller import Poller
import time

# Handles the changing state of the HeadUpAudioManager
class AudioPoller(Poller):
    enabled = False
    content = None
    update_panel_cron = None

    def enable(self):
    	if not self.enabled:
            self.enabled = True
            self.update_panel_cron = cron.interval('300ms', self.update_panel)

    def disable(self):
        self.enabled = False
        cron.cancel(self.update_panel_cron)
            
    def update_panel(self):
        pass
        
def on_ready():
    actions.user.hud_add_poller("audio", AudioPoller())

app.register("ready", on_ready)