from talon import actions, cron, app, Module
from .poller import Poller
from ..configuration import hud_get_configuration
import os
prefered_microphone = None


# Polls the current microphone state
class MicrophonePoller(Poller):
    job = None
    callbacks = {}
    
    def register(self, name, callback):
        current_callback_amount = len(self.callbacks.values())
        self.callbacks[name] = callback
        if current_callback_amount == 0:
            self.job = cron.interval("300ms", self.state_check)

    def unregister(self, name):
        if name in self.callbacks:
            del self.callbacks[name]
            
        current_callback_amount = len(self.callbacks.values())
        if current_callback_amount == 0:
            cron.cancel(self.job)
            self.job = None

    def state_check(self):
        active_mic = actions.sound.active_microphone()
        microphones = actions.sound.microphones() if "microphone_list" in self.callbacks else []
        
        callbacks = list(self.callbacks.values())[:]
        for callback in callbacks:
            callback(active_mic, microphones)

previous_mic_file = os.path.join(hud_get_configuration("content_preferences_folder"), "hud_prefered_microphone.txt")
def set_prefered_microphone(microphone):
    global prefered_microphone
    global previous_mic_file
    prefered_microphone = microphone
    with open(previous_mic_file, "w") as f:
        f.write(microphone)

def get_prefered_microphone():
    previous_mic_file
    prefered_microphone = "System Default"
    if not os.path.exists(previous_mic_file):
        set_prefered_microphone(prefered_microphone)

    with open(previous_mic_file, "r") as file:
        lines = file.readlines()
        if len(lines) > 0:
            prefered_microphone = lines[0]
    return prefered_microphone
prefered_microphone = get_prefered_microphone()

def toggle_microphone(self, _ = None):
    global prefered_microphone
    current_microphone = actions.sound.active_microphone()
    if current_microphone != "None":
        actions.sound.set_microphone("None")
    else:
        if prefered_microphone in actions.sound.microphones():
            actions.sound.set_microphone(prefered_microphone)
        else:
            actions.user.hud_add_log("warning", "Could not find " + prefered_microphone + ".\nUsing system default")
            actions.sound.set_microphone("System Default")
        
def select_microphone(choice):
    set_prefered_microphone(choice["text"])
    actions.sound.set_microphone(choice["text"])
    actions.user.hud_deactivate_poller("microphone_list")

class PartialMicrophonePoller(Poller):
    current_microphone = None
    available_microphones = []
    content = None
    enabled = False
    poller: MicrophonePoller

    def __init__(self, type, poller: MicrophonePoller):
        self.type = type
        self.poller = poller
    
    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.current_microphone = None
            self.poller.register(self.type, self.update_microphone)
    
    def update_microphone(self, active_microphone, microphones):
        if self.type == "microphone_toggle":
            if self.current_microphone != active_microphone:
                self.current_microphone = active_microphone
                if self.current_microphone == "None":
                    status_icon = self.content.create_status_icon("microphone_toggle", "microphone_off", None, "Inactive microphone", toggle_microphone)
                    self.content.publish_event("status_icons", status_icon.topic, "replace", status_icon)
                else:
                    status_icon = self.content.create_status_icon("microphone_toggle", "microphone_on", None, "Active microphone: " + self.current_microphone, toggle_microphone)
                    self.content.publish_event("status_icons", status_icon.topic, "replace", status_icon)
        else:
            # Only if there is a difference in microphone selection, change the available choices
            if len(self.available_microphones) != len(microphones) or \
                len(set(self.available_microphones) - set(microphones)) > 0 or \
                self.current_microphone != active_microphone:
                self.available_microphones = microphones

                choices = []
                for microphone in self.available_microphones:
                    mic_choice = {"text": microphone, "selected": microphone == active_microphone}
                    choices.append(mic_choice)
                
                hud_choices = self.content.create_choices(choices, select_microphone)
                content_text = "Select a microphone by saying <*option <number>/> or saying the name of the microphone"
                choice_panel_content = self.content.create_panel_content(content_text, "microphone_list", "Toolkit microphones", True, choices=hud_choices)
                self.content.publish_event("choice", "microphone_list", "replace", choice_panel_content)
            
            if self.current_microphone != active_microphone:
                self.current_microphone = active_microphone

    def disable(self):
        if self.enabled:
            self.enabled = False
            self.poller.unregister(self.type)
            if self.type == "microphone_toggle":
                self.content.publish_event("status_icons", "microphone_toggle", "remove")
            else:
                self.content.publish_event("choice", "microphone_list", "remove")

    def destroy(self):
        super().destroy()
        self.poller = None

def show_microphone_selection():
    actions.user.hud_activate_poller("microphone_list")

def add_statusbar_one_click_toggle(_ = None):
    actions.user.hud_activate_poller("microphone_toggle")
    
def remove_statusbar_one_click_toggle(_ = None):
    actions.user.hud_deactivate_poller("microphone_toggle")
    actions.user.hud_remove_status_icon("microphone_toggle")

microphone_poller = MicrophonePoller()
def register_microphone_pollers():
    global microphone_poller
    actions.user.hud_add_poller("microphone_toggle", PartialMicrophonePoller("microphone_toggle", microphone_poller))
    actions.user.hud_add_poller("microphone_list", PartialMicrophonePoller("microphone_list", microphone_poller))
    
    # Add the toggles to the status bar
    default_option = actions.user.hud_create_button("Add microphone", add_statusbar_one_click_toggle, "microphone_on")
    activated_option = actions.user.hud_create_button("Remove microphone", remove_statusbar_one_click_toggle, "microphone_on")
    status_option = actions.user.hud_create_status_option("microphone_toggle", default_option, activated_option)
    actions.user.hud_publish_status_option("microphone_toggle_option", status_option)

app.register("ready", register_microphone_pollers)

mod = Module()
@mod.action_class
class Actions:

    def show_microphone_options():
        """Show the microphone options in a choice panel"""
        show_microphone_selection()
        
    def hud_add_single_click_mic_toggle():
        """Add a single click toggle on the status bar"""
        add_statusbar_one_click_toggle()
        
    def hud_remove_single_click_mic_toggle():
        """Remove a single click toggle from the status bar"""
        remove_statusbar_one_click_toggle()
    
    def hud_toggle_microphone():
        """Toggle the HUD microphone"""
        toggle_microphone(None)