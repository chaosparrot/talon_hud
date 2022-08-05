from talon import actions, cron, app, Module, settings
from .poller import Poller
from .typing import HudAudioState
from ..speech.speech_utils import word_to_approx_vowels
import time

mod = Module()
mod.setting("talon_hud_syllable_cues", type=int, default=1, desc="Turn on syllable cues for specific contexts, default 1 for on")

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
            self.syllables_enabled = settings.get("user.talon_hud_syllable_cues") >= 1
            if self.syllables_enabled:
                self.run_syllables(event.content.message)
                
    def run_syllables(self, message: str):
        vowel_to_sound_map = {
            "e": ["Pitch mid high"],  # wEnt, ExpEnsive
            "æ": ["Pitch mid high"],  # cAt
            "ʌ": ["Pitch low mid"],   # fUn, mOney
            "ʊ": ["Pitch low"],       # lOOk, bOOt, shOUld
            "ɒ": ["Pitch mid"],       # rOb, tOrn
            "ə": ["Pitch low mid"],   # evEn
            "ɪ": ["Pitch mid"],       # sIt, kIt, Inn
            "i:": ["Pitch high"],     # nEEd, lEAn
            "ɜ:": ["Pitch low mid"],  # nUrse, sErvice, bIrd
            "ɔ:": ["Pitch mid"],      # tAlk, jAw
            "u:": ["Pitch low"],      # qUEUE
            "ɑ:": ["Pitch mid"],      # fAst, cAr
            "ɪə": ["Pitch high"],     # fEAr, bEEr
            "eə": ["Pitch mid high"], # hAIr, stAre
            "eɪ": ["Pitch mid high"], # spAce, stAIn, EIght
            "ɔɪ": ["Pitch mid high"], # jOY, fOIl
            "aɪ": ["Pitch high"],     # mY, stYle, kInd, rIght
            "əʊ": ["Pitch mid"],      # nO, blOWn, grOWn, rObe
            "aʊ": ["Pitch mid"],      # mOUth, tOWn, OUt, lOUd
        }
    
        multipliers = []
        syllables = []
        words = message.split(" ")
        for word in words:
            current_vowels = ""            
            for index, vowel in enumerate(word_to_approx_vowels(word, "en")):
                if vowel in vowel_to_sound_map:
                    for sound in vowel_to_sound_map[vowel]:
                        multipliers.append(1.0)
                        syllables.append(sound)
               
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
    actions.user.hud_add_audio_cue("Syllables", "Pitch high", "'Five' and 'near'", "4", True)
    actions.user.hud_add_audio_cue("Syllables", "Pitch mid high", "For example 'went', 'cat', 'hair', 'space' and 'joy'", "3", True)
    actions.user.hud_add_audio_cue("Syllables", "Pitch mid", "For example 'rob', 'sit', 'car', 'jaw', 'robe' and 'gown'", "2", True)
    actions.user.hud_add_audio_cue("Syllables", "Pitch low mid", "For example 'bird', 'burn', 'fun' and the last syllable in 'open'", "1", True)
    actions.user.hud_add_audio_cue("Syllables", "Pitch low", "For example 'could', 'boot' and 'queue'", "0", True)
    actions.user.hud_add_audio_cue("Syllables", "Silence", "", "silence", True)

    actions.user.hud_add_poller("syllables", syllables_poller)

app.register("ready", on_ready)

@mod.action_class
class Actions:
    
    def hud_audio_syllables_rerun():
        """Rerun the last syllables muttered by the Talon HUD"""
        rerun_syllables()
