from talon import scope, cron, app, actions, Module, Context
from talon.lib import cubeb
from .content.typing import HudAudioEvent, HudAudioGroup, HudAudioCue, HudAudioState
from .theme import HeadUpDisplayTheme
from .preferences import HeadUpDisplayUserPreferences
from .event_dispatch import HeadUpEventDispatch
from typing import Any, Union
import os
import threading
import functools
import wave
import struct

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

default_audio_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")
class HeadUpAudioManager:
    preferences: HeadUpDisplayUserPreferences = None
    theme: HeadUpDisplayTheme = None
    event_dispatch: HeadUpEventDispatch = None
    cues = None
    groups = None
    
    # Volume goes from 0 to 100 where 75 is the non-altered audio volume    
    baseline_volume = 75
    global_cue_volume = 75
    enabled = False
    
    def __init__(self):
        self.cues = {}
        self.groups = {}
    
    def start(self, preferences: HeadUpDisplayUserPreferences, theme: HeadUpDisplayTheme, event_dispatch: HeadUpEventDispatch):
        self.cues["enabled"] = HudAudioCue("default", "enabled", "HUD Audio Enabled", \
            "Trigger this sound whenever the HUD Audio is enabled", "command_mode", 75, True)
        
        self.preferences = preferences
        self.theme = theme
        self.event_dispatch = event_dispatch
        self.load_preferences(preferences)

    def set_theme(self, theme: HeadUpDisplayTheme):
        self.theme = theme

    def enable(self, persisted=False):
        if not self.enabled:
            self.enabled = True
            if persisted:
                self.audio_settings_change()
            self.trigger_cue("enabled")

    def disable(self, persisted=False):
        clear_audio()
        if self.enabled:
            self.enabled = False
            if persisted:
                self.audio_settings_change()

    def load_preferences(self, preferences: HeadUpDisplayUserPreferences):
        if "audio_volume" in preferences.prefs:
            self.global_cue_volume = min(max(0,int(preferences.prefs["audio_volume"])), 100)
            
        # Only set the enabled flag when the HUD is enabled later so we have the audio cue triggered
        if "audio_enabled" in preferences.prefs:
            self.enabled = preferences.prefs["audio_enabled"]

        for id in self.groups:
            self.load_group_preferences(self.groups[id])
        for id in self.cues:
            self.load_cue_preferences(self.cues[id])

    def load_cue_preferences(self, cue: HudAudioCue):
        audio_cue_volume_name = "audio_cue_" + cue.id + "_volume"
        audio_cue_enabled_name = "audio_cue_" + cue.id + "_enabled"
        
        if audio_cue_volume_name in self.preferences.prefs:
            cue.volume = min(max(0, int(self.preferences.prefs[audio_cue_volume_name])), 100)
        if audio_cue_enabled_name in self.preferences.prefs:
            cue.enabled = int(self.preferences.prefs[audio_cue_enabled_name]) > 0
            
    def load_group_preferences(self, group: HudAudioGroup):
        audio_group_volume_name = "audio_group_" + group.id + "_volume"
        audio_group_enabled_name = "audio_group_" + group.id + "_enabled"
        
        if audio_group_volume_name in self.preferences.prefs:
            group.volume = min(max(0, int(self.preferences.prefs[audio_group_volume_name])), 100)
        if audio_group_enabled_name in self.preferences.prefs:
            group.enabled = int(self.preferences.prefs[audio_group_enabled_name]) > 0

    def get_persistence_dict(self):
        dict = {
            "audio_volume": str(self.global_cue_volume),
            "audio_enabled": self.enabled
        }
        
        for group_id in self.groups:
            group = self.groups[group_id]
            dict["audio_group_" + group.id + "_volume"] = str(group.volume)
            dict["audio_group_" + group.id + "_enabled"] = "1" if group.enabled else "0"
        
        for cue_id in self.cues:
            cue = self.cues[cue_id]        
            dict["audio_cue_" + cue.id + "_volume"] = str(cue.volume)
            dict["audio_cue_" + cue.id + "_enabled"] = "1" if cue.enabled else "0"    
        return dict

    def audio_settings_change(self):
        audio_state = HudAudioState(self.enabled, self.global_cue_volume, list(self.groups.values()), list(self.cues.values()))
        if self.event_dispatch:
            self.event_dispatch.audio_state_change(audio_state)

    def enable_audio(self, group_id = None, cue_id = None, trigger = False):
        if group_id in self.groups and not self.groups[group_id].enabled:
            self.groups[group_id].enabled = True
            
            if trigger:
                for cue_id in self.cues:
                    if self.cues[cue_id].group == group_id and self.cues[cue_id].enabled:
                        self.trigger_cue(cue_id)
                        break
        elif cue_id in self.cues and not self.cues[cue_id].enabled:
            self.cues[cue_id].enabled = True
            
            if trigger:
                self.trigger_cue(cue_id)
        self.audio_settings_change()

    def disable_audio(self, group_id = None, cue_id = None):
        if group_id in self.groups and self.groups[group_id].enabled:
            self.groups[group_id].enabled = False
        elif cue_id in self.cues and self.cues[cue_id].enabled:
            self.cues[cue_id].enabled = False
        self.audio_settings_change()

    def set_volume(self, volume, trigger=False, group_id=None, cue_id=None):
        new_volume = min(max(0,volume), 100)
    
        if not cue_id and not group_id:
            self.global_cue_volume = new_volume
            if trigger:
                self.trigger_cue("enabled")
        elif cue_id is None and group_id is not None and group_id in self.groups:
            old_volume = self.groups[group_id].volume
            self.groups[group_id].volume = new_volume
                        
            for cue_id in self.cues:
                if self.cues[cue_id].group == group_id and \
                    self.cues[cue_id].volume > new_volume or self.cues[cue_id].volume == old_volume:
                    self.cues[cue_id].volume = new_volume
            
            if trigger:
                for cue_id in self.cues:
                    if self.cues[cue_id].group == group_id and self.cues[cue_id].enabled:
                        self.trigger_cue(cue_id)
                        break
        elif cue_id is not None and cue_id in self.cues:
            self.cues[cue_id].volume = new_volume
            if trigger:
                self.trigger_cue(cue_id)
        self.audio_settings_change()

    def register_cue(self, cue: HudAudioCue):
        if self.preferences:
            self.load_cue_preferences(cue)
        self.cues[cue.id] = cue
        
    def register_group(self, group: HudAudioGroup):
        if self.preferences:
            self.load_group_preferences(group)
        self.groups[group.id] = group

    def get_cue_path(self, cue: HudAudioCue):
        return self.theme.get_audio_path(cue.file, os.path.join(default_audio_path, cue.file + ".wav"))

    def trigger_audio(self, event: HudAudioEvent):
        for cue_index, cue_id in enumerate(event.cues):
            multiplier = 1.0
            if event.volumes is not None and cue_index < len(event.volumes):
                multiplier = event.volumes[cue_index]
            self.trigger_cue(cue_id, multiplier)

    def trigger_cue(self, id, multiplier = 1.0):
        if self.enabled and id in self.cues and self.cues[id].enabled:
            cue = self.cues[id]
            if cue.group in self.groups and not self.groups[cue.group].enabled:
                return
            
            volume = self.global_cue_volume / self.baseline_volume           
            volume = volume * cue.volume / self.baseline_volume
            volume = volume * multiplier
            
            if volume > 0:
                play_wav( self.get_cue_path(cue), volume)

    def destroy(self):
        pass

audio_manager = HeadUpAudioManager()
def register_audio_manager():
    global audio_manager
    actions.user.hud_internal_register("HeadUpAudioManager", audio_manager)

app.register("ready", register_audio_manager)

mod = Module()
@mod.action_class
class Actions:
    
    def hud_get_audio_state():
        """Get the full state of the registered audio data"""
        global audio_manager
        return HudAudioState(audio_manager.enabled, audio_manager.global_cue_volume,\
            list(audio_manager.groups.values()), list(audio_manager.cues.values()))
        
    def hud_add_audio_group(title: str, description: str, enabled: Union[bool, int] = True):
        """Add an audio group"""
        global audio_manager
        group_id = title.lower().replace(" ", "_")
        audio_manager.register_group(HudAudioGroup(group_id, title, description, 75, enabled > 0))
        
    def hud_add_audio_cue(group: str, title: str, description: str, file: str, enabled: Union[bool, int] = True):
        """Add an audio cue"""
        global audio_manager
        cue_id = title.lower().replace(" ", "_")
        group_id = group.lower().replace(" ", "_")
        audio_manager.register_cue(HudAudioCue(cue_id, group_id, title, description, file, 75, enabled > 0))
