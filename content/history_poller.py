from talon import actions, cron, scope, speech_system, ui, app
from user.talon_hud.content.poller import Poller
import time

# Handles state of phrases
# Inspired by the command history from knausj
class HistoryPoller(Poller):

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
        
        # Debugging data
        time_ms = 0.0
        timestamp = time.time()
        model = "-"
        mic = actions.sound.active_microphone()
        if "_metadata" in j:
            meta = j["_metadata"]
            time_ms += meta["total_ms"] if "total_ms" in meta else 0
            time_ms += meta["audio_ms"] if "audio_ms" in meta else 0
            model = meta["desc"] if "desc" in meta else "-"
        
        actions.user.hud_add_phrase(command, timestamp, float(time_ms), model, mic)

def on_ready():
    actions.user.hud_register_audio_cue('Command recognized', "Triggers whenever talon recognizes a command", "command_recognized", False)

app.register('ready', on_ready)