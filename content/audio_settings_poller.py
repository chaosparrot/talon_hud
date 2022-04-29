from talon import actions, cron, app, Module
from .poller import Poller
from .typing import HudAudioState
import time

# Handles the changing state of the HeadUpAudioManager
class AudioSettingsPoller(Poller):
    enabled = False
    content = None
    initialize_panel_cron = None

    def enable(self):
    	if not self.enabled:
            self.enabled = True
            self.initialize_panel_cron = cron.after('300ms', self.initialize_panel)
            if self.content:
                self.content._content.register("audio_state_change", self.update_panel)

    def disable(self):
    	if self.enabled:
            self.enabled = False
            cron.cancel(self.initialize_panel_cron)
            if self.content:
                self.content._content.unregister("audio_state_change", self.update_panel)
    
    def initialize_panel(self):
        audio_state = actions.user.hud_get_audio_state()
        panel_content = self.generate_audio_state_content(audio_state, True)
        self.content.publish_event("text", "audio_settings", "replace", panel_content, True, True)
    
    def update_panel(self, audio_state):
        panel_content = self.generate_audio_state_content(audio_state, True)
        self.content.publish_event("text", "audio_settings", "replace", panel_content, True, True)        
    
    def generate_audio_state_content(self, audio_state: HudAudioState, show=False):
        content = "Voice commands for audio management can be found inside the <*toolkit documentation/>.\n\n"
        content += "Global audio <+<*(" + str(audio_state.volume) + "/100)/>/>\n\n" if audio_state.enabled else "Global audio <!!<*muted/>/>\n\n"

        for group in audio_state.groups:
            cues_in_group = [x for x in audio_state.cues if x.group == group.id]
            if len(cues_in_group) > 0:
                content += "Group: <*" + group.title + "/>"
                content += " <+<*(" + str(group.volume) + "/100)/>/>" if group.enabled else " <!!<*muted/>/>"
                content += "\n</" + group.description + "/>\n"
                
                for cue in cues_in_group:
                    content += "* <*" +  cue.title + "/>"
                    content += " <+<*(" + str( cue.volume) + "/100)/>/>" if group.enabled and cue.enabled else " <!!<*muted/>/>"
                    if cue.description:
                        content += "\n" + cue.description + "\n"
                    else:
                        content += "\n"
        
        return self.content.create_panel_content(content, "audio_settings", "Toolkit audio", show)
        
def on_ready():
    actions.user.hud_add_audio_group("Modes", "Sounds that get triggered when a mode becomes active", True)
    actions.user.hud_add_audio_cue("Modes", "Command mode", "", "command_mode", True)
    actions.user.hud_add_audio_cue("Modes", "Dictation mode", "", "pen", True)
    actions.user.hud_add_audio_cue("Modes", "Sleep mode", "", "sleep_mode", True)

    actions.user.hud_add_poller("audio_settings", AudioSettingsPoller())

app.register("ready", on_ready)

mod = Module()
@mod.action_class
class Actions:

    def hud_show_audio_settings():
        """Display the current audio settings"""
        actions.user.hud_activate_poller("audio_settings")