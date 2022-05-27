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
            "o": ["Pitch mid"],
            "oo": ["Pitch low"],
            "uou": ["Pitch low"],            
            "ou": ["Pitch low"],
            "u": ["Pitch low"],
            "io": ["Pitch low mid"],
            "ia": ["Pitch mid high", "Pitch mid"],
            "a": ["Pitch mid"],
            "au": ["Pitch mid", "Pitch low"],            
            "ea": ["Pitch mid"],
            "e": ["Pitch mid high"],
            "ee": ["Pitch mid"],
            "ei": ["Pitch mid"],            
            "ie": ["Pitch mid"],
            "y": ["Pitch high"],
            "ai": ["Pitch mid high"],
            "oi": ["Pitch high"],
            "i": ["Pitch high"]
        }
    
        multipliers = []
        syllables = []
        words = message.split(" ")
        for word in words:
            current_vowels = ""
            if len(word) == 1:
                syllables.append("Syllable one")
                multipliers.append(1.0)
                syllables.append("Silence")
                multipliers.append(1.0)
                syllables.append("Silence")
                multipliers.append(1.0)                
            elif len(word) > 1:
                first_vowel = True
                previous_is_vowel = False
                for index, char in enumerate(word):
                    final_char = (index + 1) == len(word)
                    if char in "iaeuo":
                        current_vowels += char
                    if final_char or char not in "iaeuo":
                        if current_vowels in vowel_map:
                            if not (final_char and char == "e" and current_vowels == "e"):
                                syllable = vowel_map[current_vowels]
                                syllables.extend(vowel_map[current_vowels])
                                
                                if first_vowel:
                                    multipliers.append(1.0)
                                    for sound_index, sound in enumerate(syllable):
                                        if sound_index > 0:
                                            multipliers.append(0.4)
                                    first_vowel = False
                                else:
                                    for sound_index, sound in enumerate(syllable):
                                        multipliers.append(0.4)
                        elif final_char and char == "y":
                            syllables.extend(vowel_map[char])
                            multipliers.append(0.4)
                        current_vowels = ""
                syllables.append("Silence")
                multipliers.append(1.0)
                syllables.append("Silence")
                multipliers.append(1.0)
                syllables.append("Silence")
                multipliers.append(1.0)
        self.content.trigger_audio_cues(syllables, multipliers)        
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
    actions.user.hud_add_audio_cue("Syllables", "Pitch high", "Eye, oy in oyster", "4", True)
    actions.user.hud_add_audio_cue("Syllables", "Pitch mid high", "Ai in air, e in lend", "3", True)
    actions.user.hud_add_audio_cue("Syllables", "Pitch mid", "A in start, o in otter, ea in meat, i in switch", "2", True)
    actions.user.hud_add_audio_cue("Syllables", "Pitch low mid", "A in metal, er in mermaid", "1", True)
    actions.user.hud_add_audio_cue("Syllables", "Pitch low", "Oo in moon, o in stone, u in tube", "0", True)
    actions.user.hud_add_audio_cue("Syllables", "Silence", "", "silence", True)

    actions.user.hud_add_poller("syllables", syllables_poller, True)
    actions.user.hud_activate_poller("syllables")

app.register("ready", on_ready)

mod = Module()
@mod.action_class
class Actions:
    
    def hud_audio_syllables_rerun():
        """Rerun the last syllables muttered by the Talon HUD"""
        rerun_syllables()
