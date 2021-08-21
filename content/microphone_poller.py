from talon import actions, cron, scope, speech_system, ui, app, Module
from talon.lib import cubeb
from user.talon_hud.content.poller import Poller
from user.talon_hud.content.state import hud_content

# Polls the current microphone state
# TODO IMPROVE STABILITY
class MicrophonePoller(Poller):
    job = None
    current_microphone = False
    available_microphones = []
    
    choices_open = False
    one_click_toggle = False
    ctx = cubeb.Context()
    
    def enable(self):
        self.enabled = True
        if (self.job is None):
            self.current_microphone = actions.sound.active_microphone()        
            self.set_available_microphones()
            content = {
                'active_microphone': self.current_microphone
            }
            self.job = cron.interval('300ms', self.state_check)
            hud_content.update(content)

    def disable(self):
        self.enabled = False
        cron.cancel(self.job)
        self.job = None

    def state_check(self):
        microphone_change = actions.sound.active_microphone()
        if microphone_change != self.current_microphone:
            self.current_microphone = microphone_change
            content = {
                'active_microphone': self.current_microphone
            }
            
            hud_content.update(content)

    def set_available_microphones(self):
        self.available_microphones = actions.sound.microphones()
        
    def get_microphone_options(self):
        choices = []
        for microphone in self.available_microphones:
            mic_choice = {"text": microphone, "selected": microphone == self.current_microphone}
            choices.append(mic_choice)
        return choices
        
        
poller = MicrophonePoller()

def select_microphone(choice):
    actions.sound.set_microphone(choice["text"])
    poller.choices_open = False
    
    if not poller.choices_open and not poller.one_click_toggle:
       actions.user.hud_remove_poller('microphone')

def show_microphone_selection():
    if not poller.one_click_toggle:
        actions.user.hud_remove_poller('microphone')
        actions.user.hud_add_poller('microphone', poller, True)
        actions.user.hud_activate_poller('microphone')
    poller.choices_open = True
    
    choices = actions.user.hud_create_choices(poller.get_microphone_options(), select_microphone)
    actions.user.hud_publish_choices(choices, "Toolkit microphones", "Select a microphone by saying <*option <number>/> or saying the name of the microphone")
    
def add_statusbar_one_click_toggle():
    if not poller.one_click_toggle:
        actions.user.hud_widget_subscribe_topic("status_bar", "active_microphone")
        actions.user.hud_refresh_content()
    
        if not poller.choices_open:
            actions.user.hud_remove_poller('microphone')    
            actions.user.hud_add_poller('microphone', poller, True)
            actions.user.hud_activate_poller('microphone')

    poller.one_click_toggle = True
    
def remove_statusbar_one_click_toggle():
    actions.user.hud_widget_unsubscribe_topic("status_bar", "active_microphone")
    actions.user.hud_refresh_content()
    poller.one_click_toggle = False
    
    if not poller.choices_open and not poller.one_click_toggle:
       actions.user.hud_remove_poller('microphone')

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
