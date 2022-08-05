from talon import actions, cron, app, Module
from .poller import Poller
from .typing import HudAudioState
import time

# Generates sounds based on the current modes, mic status and audio status
class AudioStatusPoller:
    current_mode = ""
    current_mic = False
    status_check_job = None
    callbacks = {}

    def register(self, name, callback):
        current_callback_amount = len(self.callbacks.values())
        self.callbacks[name] = callback
        if (current_callback_amount == 0):
            self.status_check_job = cron.interval("300ms", self.status_check)

        # When both pollers are registered, automatically do a status check 
        # For fast feedback during audio enabling
        else:
            self.status_check()

    def unregister(self, name):
        if name in self.callbacks:
            del self.callbacks[name]
        
        self.previous_mode = None
        current_callback_amount = len(self.callbacks.values())
        if (current_callback_amount == 0):
            cron.cancel(self.status_check_job)
            self.status_check_job = None

    def status_check(self, forced = False):
        active_mic = actions.sound.active_microphone()
        mic_changed = active_mic != self.current_mic or forced
        if mic_changed:
            self.current_mic = active_mic

            callbacks = list(self.callbacks.values())[:]
            for callback in callbacks:
                callback(active_mic, None)
        
        if active_mic != "None":
            current_mode = actions.user.hud_determine_mode()            
            if current_mode.startswith("user."):
                current_mode = current_mode[5:]
            if current_mode != self.current_mode or mic_changed or forced:
                self.current_mode = current_mode
                callbacks = list(self.callbacks.values())[:]
                for callback in callbacks:
                    callback(None, current_mode)

class PartialAudioStatusPoller(Poller):
    enabled = False
    content = None
    
    def __init__(self, type: str, poller: AudioStatusPoller):
        self.type = type
        self.poller = poller
    
    def enable(self):
    	if not self.enabled:
            self.enabled = True
            if self.type == "Microphone status":
                self.poller.register(self.type, self.update_microphone)
            else:
                self.poller.register(self.type, self.update_modes)

    def disable(self):
    	if self.enabled:
            self.enabled = False
            self.poller.unregister(self.type)

    def update_microphone(self, active_mic: str, mode: str):
        if active_mic != None:
            if active_mic == "None":
                self.content.trigger_audio_cue("No mic")
            else:
                self.content.trigger_audio_cue("Switch mic")

    def update_modes(self, active_mic: str, mode: str):
        if mode != None:
            self.content.trigger_audio_cue(mode.capitalize() + " mode")
    
    def destroy(self):
       self.disable(self)
       self.poller = None

audio_status_poller = AudioStatusPoller()

def trigger_audio_status():
    global audio_status_poller
    audio_status_poller.status_check(True)

def on_ready():
    global audio_status_poller
    
    actions.user.hud_add_audio_group("Modes status", "Sounds that get triggered when a mode becomes active", True)
    status_modes = actions.user.hud_get_status_modes()
    for status_mode in status_modes:
        if status_mode.startswith("user."):
            status_mode = status_mode[5:]
        actions.user.hud_add_audio_cue("Modes status", status_mode.capitalize() + " mode", "", status_mode + "_mode", True)

    actions.user.hud_add_audio_group("Microphone status", "Status changes for microphones", True)
    actions.user.hud_add_audio_cue("Microphone status", "No mic", "", "mic_none", True)
    actions.user.hud_add_audio_cue("Microphone status", "Switch mic", "", "mic_on", False)
    actions.user.hud_add_poller("modes_status", PartialAudioStatusPoller("Modes status", audio_status_poller))
    actions.user.hud_add_poller("microphone_status", PartialAudioStatusPoller("Microphone status", audio_status_poller))

app.register("ready", on_ready)

mod = Module()
@mod.action_class
class Actions:
    
    def hud_audio_status_sounds():
        """Trigger the current status of Talon as audio cues"""
        trigger_audio_status()