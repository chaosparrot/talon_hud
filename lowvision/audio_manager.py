from talon import scope, cron, app, actions, Module, Context
from ..content.typing import HudAudioCue
from ..theme import HeadUpDisplayTheme
from ..preferences import HeadUpDisplayUserPreferences
import os
from ._wav import play_wav, clear_audio

default_audio_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")

class HeadUpAudioManager:
    preferences: HeadUpDisplayUserPreferences = None
    theme: HeadUpDisplayTheme = None
    
    cues = {}
    
    # Volume goes from 0 to 100 where 75 is the non-altered audio volume    
    baseline_volume = 75
    global_cue_volume = 75
    enabled = False
    
    def __init__(self, preferences: HeadUpDisplayUserPreferences, theme: HeadUpDisplayTheme):
        self.cues['enabled'] = HudAudioCue("enabled", "HUD Enabled", \
            "Trigger this sound whenever the HUD is enabled", "command_mode", 75, True)
        
        self.preferences = preferences
        self.theme = theme
        self.load_preferences(preferences, True)

    def set_theme(self, theme: HeadUpDisplayTheme):
        self.theme = theme

    def enable(self, persisted=False):
        if not self.enabled:
            self.enabled = True
            if persisted:
                self.preferences.persist_preferences({'audio_enabled': "1"})
            self.trigger_cue("enabled")

    def disable(self, persisted=False):
        self.enabled = False
        clear_audio()
        if persisted:
            self.preferences.persist_preferences({'audio_enabled': "0"})

    def load_preferences(self, preferences: HeadUpDisplayUserPreferences, initial=False):
        if "audio_cue_volume" in preferences.prefs:
            self.global_cue_volume = min(max(0,int(preferences.prefs["audio_cue_volume"])), 100)
            
        # Only set the enabled flag when the HUD is enabled later so we have the audio cue triggered
        if not initial and "audio_enabled" in preferences.prefs:
            self.enabled = preferences.prefs["audio_enabled"]

        for id in self.cues:
            self.load_cue_preferences(self.cues[id])

    def load_cue_preferences(self, cue: HudAudioCue):
        audio_cue_volume_name = "audio_cue_" + cue.id + "_volume"
        audio_cue_enabled_name = "audio_cue_" + cue.id + "_enabled"
        
        if audio_cue_volume_name in self.preferences.prefs:
            cue.volume = min(max(0, int(self.preferences.prefs[audio_cue_volume_name])), 100)
        if audio_cue_enabled_name in self.preferences.prefs:
            cue.enabled = int(self.preferences.prefs[audio_cue_enabled_name]) > 0

    def persist_preferences(self):
        dict = {
            "audio_cue_volume": str(self.global_cue_volume),
            "audio_enabled": "1" if self.enabled else "0"
        }
        
        for id in self.cues:
            cue = self.cues[id]
            dict["audio_cue_" + id + "_volume"] = str(cue.volume)
            dict["audio_cue_" + id + "_enabled"] = "1" if cue.enabled else "0"
        self.preferences.persist_preferences(dict)

    def enable_id(self, id, trigger = False):
        if id in self.cues and not self.cues[id].enabled:
            self.cues[id].enabled = True
            self.preferences.persist_preferences({"audio_cue_" + id + "_enabled": "1"})
            
            if trigger:
                self.trigger_cue(id)
            
    def disable_id(self, id):
        if id in self.cues and self.cues[id].enabled:
            self.cues[id].enabled = False
            self.preferences.persist_preferences({"audio_cue_" + id + "_enabled": "0"})

    def set_volume(self, cue_volume, trigger=False, id=None):
        if not id:        
            self.global_cue_volume = min(max(0,cue_volume), 100)
            self.preferences.persist_preferences({"audio_cue_volume": str(self.global_cue_volume)})
            if trigger:
                self.trigger_cue("enabled")
            
        elif id in self.cues:
            self.cues[id].volume = min(max(0,cue_volume), 100)
            self.preferences.persist_preferences({"audio_cue_" + id + "_volume": str(self.global_cue_volume)})
            if trigger:
                self.trigger_cue(id)

    def register_cue(self, cue: HudAudioCue):
        self.load_cue_preferences(cue)
        self.cues[cue.id] = cue
                
    def unregister_cue(self, cue: HudAudioCue):
        del self.cues[cue.id]

    def get_cue_path(self, cue: HudAudioCue):
        return self.theme.get_audio_path(cue.file, os.path.join(default_audio_path, cue.file + ".wav"))

    def trigger_cue(self, id):
        if self.enabled and id in self.cues and self.cues[id].enabled:
            cue = self.cues[id]
            volume = self.global_cue_volume / 75 * cue.volume / 75
            if volume > 0:
                play_wav( self.get_cue_path(cue), volume)