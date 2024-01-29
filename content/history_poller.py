from talon import actions, cron, scope, speech_system, ui, app
from .poller import Poller
import time

# Handles state of phrases
# Inspired by the command history from knausj
class HistoryPoller(Poller):
    enabled = False
    content = None

    def enable(self):
    	if not self.enabled:
            self.enabled = True
            speech_system.register("phrase", self.on_phrase)

    def disable(self):
        self.enabled = False    
        speech_system.unregister("phrase", self.on_phrase)
            
    def on_phrase(self, j):
        command = actions.user.history_transform_phrase_text(j.get("text"))

        if command is None:
            return

        self.content.add_log("command", command)
        
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
        
        metadata = {
            "phrase": command,
            "time_ms": time_ms,
            "timestamp": timestamp,
            "model": model,
            "microphone": mic
        }
        
        self.content.add_log("phrase", command, timestamp, metadata)
        
def on_ready():
    # This poller needs to be kept alive so that the phrases are properly registered
    actions.user.hud_add_poller("history", HistoryPoller(), True)

app.register("ready", on_ready)