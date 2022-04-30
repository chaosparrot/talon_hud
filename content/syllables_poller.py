from talon import actions, cron, app, Module
from .poller import Poller
from .typing import HudAudioState
import time

# Generates sounds mimicking syllables according to the commands said
class SyllablesPoller(Poller):
    audio_enabled = True
    enabled = False
    content = None
    last_message = None
    syllables_enabled = False

    def enable(self):
    	if not self.enabled:
            self.enabled = True
            self.syllables_enabled = True
            if self.content:
                self.content._content.register("broadcast_update", self.on_broadcast_update)
                self.content._content.register("audio_state_change", self.audio_update)

    def disable(self):
    	if self.enabled:
            self.enabled = False
            self.syllables_enabled = False
            if self.content:
                self.content._content.unregister("audio_state_change", self.audio_update)
                self.content._content.unregister("broadcast_update", self.on_broadcast_update)                
                

    def on_broadcast_update(self, event):
        if event.topic_type == "log_messages" and event.topic == "phrase":
            self.run_syllables(event.content.message)
                
    def run_syllables(self, message: str):
        vowel_map = {
            "o": "Syllable one",
            "oo": "Syllable one",
            "ou": "Syllable one",            
            "u": "Syllable one",
            "a": "Syllable two",
            "ai": "Syllable two",
            "ea": "Syllable two",
            "e": "Syllable three",
            "ee": "Syllable three",
            "ie": "Syllable three",
            "y": "Syllable three",
            "ai": "Syllable four",
            "oi": "Syllable four",
            "i": "Syllable four"
        }
    
        # TODO DETERMINE SYLLABLES
        # TODO TRIGGER SYLLABLES
        syllables = []
        words = message.split(" ")
        for word in words:
            current_vowels = ""
            if len(word) == 1:
                syllables.append("Syllable one")
                syllables.append("Silence")
                syllables.append("Silence")
            elif len(word) > 1:
                previous_is_vowel = False
                for index, char in enumerate(word):
                    final_char = (index + 1) == len(word)
                    if char in "iaeuo":
                        current_vowels += char
                    if final_char or char not in "iaeuo":
                        if current_vowels in vowel_map:
                            if not (final_char and char == "e" and current_vowels == "e"):
                                syllables.append(vowel_map[current_vowels])
                                syllables.append("Silence")
                        elif final_char and char == "y":
                            syllables.append(vowel_map[char])
                            syllables.append("Silence")
                        current_vowels = ""
                syllables.append("Silence")
                syllables.append("Silence")
        self.content.trigger_audio_cues(syllables)        
        self.last_message = message
                
    def audio_update(self, audio_state):
        if self.audio_enabled != audio_state.enabled:
            self.audio_enabled = audio_state.enabled
            # Enabled syllables
            if audio_state.enabled and not self.syllables_enabled:
                self.content._content.register("broadcast_update", self.on_broadcast_update)
            # Disable syllables if the audio is muted anyway
            elif self.syllables_enabled:
                self.content._content.unregister("broadcast_update", self.on_broadcast_update)
            self.syllables_enabled = audio_state.enabled
    
    def rerun_syllables(self):
        if self.last_message:
            self.run_syllables(self.last_message)
    
    def destroy(self):
       self.disable(self)

syllables_poller = SyllablesPoller()

def rerun_syllables():
    global syllables_poller
    syllables_poller.rerun_syllables()

def on_ready():
    global syllables_poller
    
    actions.user.hud_add_audio_group("Syllables", "Mimicks the syllables of a voice command said", False)
    actions.user.hud_add_audio_cue("Syllables", "Silence", "", "silence", True)    
    actions.user.hud_add_audio_cue("Syllables", "Syllable one", "", "1", True)
    actions.user.hud_add_audio_cue("Syllables", "Syllable two", "", "2", True)
    actions.user.hud_add_audio_cue("Syllables", "Syllable three", "", "3", True)
    actions.user.hud_add_audio_cue("Syllables", "Syllable four", "", "4", True)

    actions.user.hud_add_poller("syllables", syllables_poller, True)
    actions.user.hud_activate_poller("syllables")

app.register("ready", on_ready)

mod = Module()
@mod.action_class
class Actions:
    
    def hud_audio_syllables_rerun():
        """Rerun the last syllables muttered by the Talon HUD"""
        rerun_syllables()