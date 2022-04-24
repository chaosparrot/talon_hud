from talon import scope, cron, app, actions, Module, Context
from talon.lib import cubeb
from .content.typing import HudAudioCue
from .theme import HeadUpDisplayTheme
from .preferences import HeadUpDisplayUserPreferences
import os
import threading
import functools
import wave
import struct

default_audio_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")

class HeadUpAudioManager:
    preferences: HeadUpDisplayUserPreferences = None
    theme: HeadUpDisplayTheme = None
    
    cues = {}
    cue_type = {}
    
    # Volume goes from 0 to 100 where 75 is the non-altered audio volume    
    baseline_volume = 75
    global_cue_volume = 75
    enabled = False
    
    def start(self, preferences: HeadUpDisplayUserPreferences, theme: HeadUpDisplayTheme):
        self.cues["enabled"] = HudAudioCue("enabled", "HUD Enabled", \
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
                self.preferences.persist_preferences({"audio_enabled": "1"})
            self.trigger_cue("enabled")

    def disable(self, persisted=False):
        self.enabled = False
        clear_audio()
        if persisted:
            self.preferences.persist_preferences({"audio_enabled": "0"})

    def load_preferences(self, preferences: HeadUpDisplayUserPreferences, initial=False):
        if "audio_cue_volume" in preferences.prefs:
            self.global_cue_volume = min(max(0,int(preferences.prefs["audio_cue_volume"])), 100)
            
        # Only set the enabled flag when the HUD is enabled later so we have the audio cue triggered
        if not initial and "audio_enabled" in preferences.prefs:
            self.enabled = preferences.prefs["audio_enabled"]

        # Reload 
        for pref in preferences.prefs:
            if pref.startswith("audio_cue_"):
                id = pref.replace("audio_cue_", "").replace("_enabled", "").replace("_volume", "")        
                if id not in self.cues:
                    if not id in self.cue_types:
                        self.cue_types[id] = {"enabled": True, "volume": self.baseline_volume}
                    
                    if pref.endswith("_enabled"):
                        self.cue_types[id]["enabled"] = int(preferences.prefs[pref]) > 0
                    elif pref.endswith("_volume"):
                        self.cue_types[id]["volume"] = min(max(0, int(preferences.prefs[pref])), 100)

        for id in self.cues:
            self.load_cue_preferences(self.cues[id])

    def load_cue_preferences(self, cue: HudAudioCue):
        audio_cue_volume_name = "audio_cue_" + cue.id + "_volume"
        audio_cue_enabled_name = "audio_cue_" + cue.id + "_enabled"
        
        if audio_cue_volume_name in self.preferences.prefs:
            cue.volume = min(max(0, int(self.preferences.prefs[audio_cue_volume_name])), 100)
        if audio_cue_enabled_name in self.preferences.prefs:
            cue.enabled = int(self.preferences.prefs[audio_cue_enabled_name]) > 0
            
    def load_cue_type_preferences(self, cue_type: str):
        audio_cue_type_volume_name = "audio_cue_" + cue_type + "_volume"
        audio_cue_type_enabled_name = "audio_cue_" + cue_type + "_enabled"
        
        cue_type_object = {
            "volume": self.baseline_volume,
            "enabled": True
        }
        if audio_cue_volume_name in self.preferences.prefs:
            cue_type_object["volume"] = min(max(0, int(self.preferences.prefs[audio_cue_volume_name])), 100)
        if audio_cue_type_enabled_name in self.preferences.prefs:
            cue_type_object["enabled"] = int(self.preferences.prefs[audio_cue_type_enabled_name]) > 0
        self.cue_type[cue_type] = cue_type_object

    def persist_preferences(self):
        dict = {
            "audio_cue_volume": str(self.global_cue_volume),
            "audio_enabled": "1" if self.enabled else "0"
        }
        
        for type in self.cue_types:
            cue_type = self.cue_types[type]
            dict["audio_cue_" + type + "_volume"] = str(cue_type["volume"])
            dict["audio_cue_" + type + "_enabled"] = "1" if cue_type["enabled"] else "0"
            
        for id in self.cues:
            cue = self.cues[id]
            dict["audio_cue_" + id + "_volume"] = str(cue.volume)
            dict["audio_cue_" + id + "_enabled"] = "1" if cue.enabled else "0"
        self.preferences.persist_preferences(dict)

    def enable_audio(self, type, id = None, trigger = False):
        if id is None:
            self.cue_types[type]["enabled"] = False
            self.preferences.persist_preferences({"audio_cue_" + type + "_enabled": "1"})
    
            if trigger:
                self.trigger_cue("enabled") # TODO TRIGGER FIRST ITEM IN CUE TYPE    
    
        elif id in self.cues and not self.cues[id].enabled:
            self.cues[id].enabled = True
            self.preferences.persist_preferences({"audio_cue_" + id + "_enabled": "1"})
            
            if trigger:
                self.trigger_cue(id)

    def disable_audio(self, type, id = None):
        if id is None:
            self.cue_types[type]["enabled"] = False
            self.preferences.persist_preferences({"audio_cue_" + type + "_enabled": "0"})

        elif id in self.cues and self.cues[id].enabled:
            self.cues[id].enabled = False
            self.preferences.persist_preferences({"audio_cue_" + id + "_enabled": "0"})

    def set_volume(self, cue_volume, trigger=False, type=None, id=None):
        if not id and not type:
            self.global_cue_volume = min(max(0,cue_volume), 100)
            self.preferences.persist_preferences({"audio_cue_volume": str(self.global_cue_volume)})
            if trigger:
                self.trigger_cue("enabled")
        elif id is None and type is not None and type in self.cue_types:
            self.cue_type[type]["volume"] = min(max(0,cue_volume), 100)
            self.preferences.persist_preferences({"audio_cue_" + type + "_volume": str(self.cue_type[type]["volume"])})            
            
            if trigger:
                self.trigger_cue("enabled") # TODO FIND FIRST CUE AND TRIGGER IT
        elif id is not None and id in self.cues:
            self.cues[id].volume = min(max(0,cue_volume), 100)
            self.preferences.persist_preferences({"audio_cue_" + id + "_volume": str(self.global_cue_volume)})
            if trigger:
                self.trigger_cue(id)

    def register_cue(self, cue: HudAudioCue):
        self.load_cue_preferences(cue)
        self.load_cue_type_preferences(cue.type)
        self.cues[cue.id] = cue

    def unregister_cue(self, cue: HudAudioCue):
        del self.cues[cue.id]

    def get_cue_path(self, cue: HudAudioCue):
        return self.theme.get_audio_path(cue.file, os.path.join(default_audio_path, cue.file + ".wav"))

    def trigger_cue(self, id):
        if self.enabled and id in self.cues and self.cues[id].enabled:
            cue = self.cues[id]
            if not self.cue_type_volume[cue.type]["enabled"]:
                return
            
            volume = self.global_cue_volume / self.baseline_volume           
            if cue.type in self.cue_type:
                volume = volume * self.cue_type_volume[cue.type]["volume"] / self.baseline_volume
            volume = volume * cue.volume / self.baseline_volume
            if volume > 0:
                play_wav( self.get_cue_path(cue), volume)

audio_manager = HeadUpAudioManager()
def register_audio_manager():
    global audio_manager
    actions.user.hud_internal_register("HeadUpAudioManager", audio_manager)

app.register("ready", register_audio_manager)

"""Module for playing wav files in Talon.
Only works with 16-bit signed wavs. Not designed to work with spamming.
Author: Ryan Hileman (lunixbochs).
Modified by GitHub user Jcaw, and again by Github user chaosparrot.
""" 
class _WavSource:
    def __init__(self, path, volume=1): 
        self.path = path
        try:
            wav_file = wave.open(path)
            self.params = wav_file.getparams()
            if self.params.sampwidth != 2:
                raise Exception("only 16-bit signed PCM supported")
            nframes = self.params.nframes
            frames = wav_file.readframes(nframes)
            self.samples = struct.unpack(
                "<{}h".format(nframes * self.params.nchannels), frames
            )
            self.samplerate = self.params.framerate
            self.channels = self.params.nchannels
            if self.channels == 2:
                self.samples = self.samples[::2]
                self.channels = 1
            
            # Adjust the volume of this source
            volume_adjusted_samples = []
            for sample in self.samples:
                volume_adjusted_samples.append(int(sample * volume))
            self.samples = volume_adjusted_samples
            
        finally:
            wav_file.close()

class _Player:
    def __init__(self, rate, fmt, channels):
        self.lock = threading.Lock()
        self.ctx = cubeb.Context()
        params = cubeb.StreamParams(rate=rate, format=fmt, channels=channels)
        self.buffer = []
        self.stream = self.ctx.new_output_stream(
            "player", None, params, latency=-1, data_cb=self._source
        )
        self.stream.start()

    def _source(self, stream, samples_in, samples_out):
        needed = len(samples_out)
        with self.lock:
            if len(self.buffer) > 0:
                frame = self.buffer[:needed]
                if len(frame) < needed:
                    frame += [0] * (needed - len(frame))
                samples_out[:] = frame
                self.buffer = self.buffer[needed:]
                return needed
        return needed

    def append(self, samples):
        with self.lock:
            self.buffer += samples
            
    def clear(self):
        with self.lock:
            self.buffer = []
            
# Cache to avoid repeated, slow disk I/O
@functools.lru_cache(maxsize=32)
def load_wav(path, volume=1):
    return _WavSource(path, volume)

_players = {}

def clear_audio():
    player_key = (44100, 1)
    player = _players.get(player_key)
    if player:
        player.clear()

def play_wav(path, volume=1):
    global _players
    wav = load_wav(path, volume)
    # Player seems to leak. Creating many players eventually causes audio to
    # corrupt. We can re-use old players to prevent it.
    #
    # NOTE this will play identically sampled wavs one by one, but differently
    # sampled wavs in parallel.
    #
    # TODO: Allow multiple wavs to be played at once without corrupting.
    player_key = (wav.samplerate, wav.channels)
    player = _players.get(player_key)
    if not player:
        player = _Player(wav.samplerate, cubeb.SampleFormat.S16LE, wav.channels)
        _players[player_key] = player
    player.append(wav.samples)
    return player