from talon import actions, cron, scope, speech_system, ui, app
from user.talon_hud.content.poller import Poller
from talon_plugins import menu

# Handles state of phrases
# Inspired by the command history from knausj
class HistoryPoller(Poller):
    commands = []

    def enable(self):
    	if not self.enabled:
            self.enabled = True
            speech_system.register("phrase", self.on_phrase)

    def disable(self):
        self.enabled = False    
        speech_system.unregister("phrase", self.on_phrase)
            
    def on_phrase(self, j):
        try:
            word_list = getattr(j["parsed"], "_unmapped", j["phrase"])
        except:
            word_list = j["phrase"]
        command = " ".join(word.split("\\")[0] for word in word_list)        
        actions.user.hud_add_log("command", command)