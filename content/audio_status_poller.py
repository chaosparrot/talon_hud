from talon import actions, cron, app, Module
from .poller import Poller
from .typing import HudAudioState
import time

# Generates sounds based on the current modes, mic status and audio status
class AudioStatusPoller(Poller):
    enabled = False
    content = None
    status_check_job = None

    audio_enabled = True
    current_mode = ""
    current_mic = False

    def enable(self):
    	if not self.enabled:
            self.enabled = True
            self.status_check_job = cron.interval('300ms', self.status_check)
            if self.content:
                self.content._content.register("audio_state_change", self.audio_update)

    def disable(self):
    	if self.enabled:
            self.enabled = False
            cron.cancel(self.status_check_job)
            if self.content:
                self.content._content.unregister("audio_state_change", self.audio_update)
                
    def audio_update(self, audio_state):
        if self.audio_enabled != audio_state.enabled:
            if audio_state.enabled:
                self.status_check(True)
                self.status_check_job = cron.interval('300ms', self.status_check)
            # Disable status check if the audio is muted anyway
            else:
                cron.cancel(self.status_check_job)
    
    def status_check(self, forced = False):
        active_mic = actions.sound.active_microphone()
        mic_changed = active_mic != self.current_mic
        if mic_changed:
            self.current_mic = active_mic
            if active_mic == "None" or forced:
                self.content.trigger_audio_cue("No mic")
            else:
                self.content.trigger_audio_cue("Switch mic")        
        
        if active_mic != "None":
            current_mode = actions.user.hud_determine_mode()
            if current_mode.startswith("user."):
                current_mode = current_mode[5:]
            if current_mode != self.current_mode or mic_changed or forced:
                self.current_mode = current_mode
                self.content.trigger_audio_cue(current_mode.capitalize() + " mode")

    def destroy(self):
       self.disable(self)
       self.audio_enabled = True
       self.current_mode = ""
       self.current_mic = "None"

audio_status_poller = AudioStatusPoller()

def trigger_audio_status():
    global audio_status_poller
    audio_status_poller.status_check(True)

def on_ready():
    global audio_status_poller
    
    actions.user.hud_add_audio_group("Modes", "Sounds that get triggered when a mode becomes active", True)
    status_modes = actions.user.hud_get_status_modes()
    for status_mode in status_modes:
        if status_mode.startswith("user."):
            status_mode = status_mode[5:]
        actions.user.hud_add_audio_cue("Modes", status_mode.capitalize() + " mode", "", status_mode + "_mode", True)

    actions.user.hud_add_audio_group("Microphone", "Status changes for microphones", True)
    actions.user.hud_add_audio_cue("Microphone", "No mic", "", "mic_none", True)
    actions.user.hud_add_audio_cue("Microphone", "Switch mic", "", "mic_on", False)

    actions.user.hud_add_poller("audio_status", audio_status_poller, True)
    actions.user.hud_activate_poller("audio_status")

app.register("ready", on_ready)

mod = Module()
@mod.action_class
class Actions:
    
    def hud_audio_status_sounds():
        """Trigger the current status of Talon as audio cues"""
        trigger_audio_status()