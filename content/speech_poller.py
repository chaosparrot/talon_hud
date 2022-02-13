from talon import actions, cron, scope, ui, app, Module, settings
from talon_init import TALON_HOME
from .poller import Poller
import datetime
import os
import platform
import subprocess

class SpeechPoller(Poller):
    content = None
    enabled = False
    last_phrase_time = 0

    def enable(self):
    	if not self.enabled:
            self.enabled = True
            if self.content is None or self.content._content is None or self.content._content.topic_types is None:
                return

            self.content._content.register("broadcast_update", self.on_broadcast_update)
            self.generate_phrase_debug_content()

    def disable(self):
        if self.enabled:
            self.enabled = False
            if self.content is None or self.content._content is None or self.content._content.topic_types is None:
                return
            
            self.content._content.unregister("broadcast_update", self.on_broadcast_update)
        
    def on_broadcast_update(self, event):
        if event.topic_type == "log_messages" and event.topic == "phrase":
            self.generate_phrase_debug_content()
            
    def generate_phrase_debug_content(self):
        if self.content is None or self.content._content is None or self.content._content.topic_types is None:
            return
    
        phrases = self.content._content.topic_types["log_messages"]["phrase"] if "phrase" in self.content._content.topic_types["log_messages"] else []

        last_mic = ""
        last_model = ""
        content = ""
        if len(phrases) == 0:
            content = "No speech data collected yet"
        else:
            last_phrase = phrases[len(phrases) - 1].metadata
            content += "<*" + last_phrase["phrase"] + "/> (" + self.format_time_ms(last_phrase["time_ms"]) + ")\n"
            content += "[<+<*" + last_phrase["microphone"]
            content += "/>/> with <@<*" + last_phrase["model"] + "]/>/>\n------------\n"
            last_mic = last_phrase["microphone"]
            last_model = last_phrase["model"]
            
        last_time_str = ""
        for phrase in phrases:
            phrase = phrase.metadata
            metadata = []
            time_str = datetime.datetime.fromtimestamp(int(phrase["timestamp"])).strftime("%H:%M")
            if time_str != last_time_str:
               metadata.append(time_str)
               last_time_str = time_str
            
            if last_mic != phrase["microphone"]:
               metadata.append("<+<*" + phrase["microphone"] + "/>/>")
               last_mic =phrase["microphone"]

            if last_model != phrase["model"]:
               metadata.append("<@<*" + phrase["model"] + "/>/>")
               last_model = phrase["model"]
            
            if len(metadata) > 0:
               content += "[" + ", ".join(metadata) + "]\n"
            
            content += "- <*" + phrase["phrase"] + "/>"
            time_s = self.format_time_ms(phrase["time_ms"], 2000)
            if time_s:
               content += " (" + time_s + ")"
            
            content += "\n"

        buttons = []
        buttons.append(self.content.create_button("Show recordings", self.open_recordings))
        panel_content = self.content.create_panel_content(content, "speech", "Toolkit speech", True, buttons)
        self.content.publish_event("text", panel_content.topic, "replace", panel_content, True, True)
        
    def open_recordings(self, data):
        if settings.get("speech.record_all", False) == False:
            actions.user.hud_add_log("warning", "Recordings aren't currently enabled!\n" + \
            "Enable them in the talon menu to create recordings")
            
        if not os.path.exists(str(TALON_HOME) + "/recordings"):
            actions.user.hud_add_log("error", "No recordings have been made yet!")        
        else:
            recordings_folder = str(TALON_HOME)
            recordings_folder += "/recordings"            
            if platform.system() == "Windows":
                os.startfile(recordings_folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", recordings_folder])
            else:
                subprocess.Popen(["xdg-open", recordings_folder])

        
    def format_time_ms(self, time_ms: float, threshold: float = 0.0) -> str:    
        content = ""
        if  time_ms <= threshold:
            return content
        
        if time_ms >= 7500:
            if time_ms >= 20000:
                content += "<!!"            
            else:
                content += "<!"
        content += "{:.1f}".format(time_ms / 1000) + "s"        
        if time_ms >= 7500:
            content += "/>"
        return content


def register_poller():
    actions.user.hud_add_poller("speech", SpeechPoller())

app.register("ready", register_poller)

mod = Module()
@mod.action_class
class Action:

    def hud_toolkit_speech():
        """Start displaying the phrase debugging tools"""
        actions.user.hud_activate_poller("speech")