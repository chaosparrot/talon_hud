from talon import Context, Module, actions, app, skia, cron, ctrl, scope, canvas, registry, settings, ui
import os
import time
import numpy

from user.talon_hud.preferences import HeadUpDisplayUserPreferences
from user.talon_hud.theme import HeadUpDisplayTheme
from user.talon_hud.state import hud_content
from user.talon_hud.widgets.statusbar import HeadUpStatusBar
from user.talon_hud.widgets.eventlog import HeadUpEventLog

ctx = Context()
mod = Module()

class HeadUpDisplay:
    enabled = False
    display_state = None
    preferences = None
    theme = None
    poller = None
    disable_poller_job = None
    show_animations = False
    widgets = []
    
    prev_mouse_pos = None
    mouse_poller = None
    
    def __init__(self, display_state, preferences, poller = None):
        self.display_state = display_state
        self.preferences = preferences
        self.poller = poller
        self.disable_poller_job = None
        self.theme = HeadUpDisplayTheme(self.preferences.prefs['theme_name'])
        self.show_animations = self.preferences.prefs['show_animations']
        self.widgets = [
            HeadUpStatusBar('status_bar', self.preferences, self.theme),
            HeadUpEventLog('event_log', self.preferences, self.theme),
        ]
        if (self.preferences.prefs['enabled']):
            self.enable()
            
    def enable(self):
        if not self.enabled:
            self.enabled = True
            if self.poller:
                self.poller.enable()
                
            for widget in self.widgets:
                # TODO RESPECT WIDGET USER ENABLED STATE
                if not widget.enabled:
                    widget.enable(self.show_animations)
            
            self.display_state.register('content_update', self.content_update)
            self.display_state.register('log_update', self.log_update)
            self.mouse_poller = cron.interval('100ms', self.poll_mouse_pos)            
            self.preferences.persist_preferences({'enabled': True})

    def disable(self):
        if self.enabled:
            self.enabled = False
            
            # TODO RESPECT WIDGET USER ENABLED STATE            
            for widget in self.widgets:
                if widget.enabled:
                    widget.disable(self.show_animations)
            
            if self.poller:
                self.disable_poller_job = cron.interval('30ms', self.disable_poller_check)                
            
            if self.mouse_poller:
                cron.cancel(self.mouse_poller)            
                self.mouse_poller = None
            
            self.display_state.unregister('content_update', self.content_update)
            self.display_state.unregister('log_update', self.log_update)            
            self.preferences.persist_preferences({'enabled': False})
    
    def enable_id(self, id):
        for widget in self.widgets:
            if not widget.enabled and widget.id == id:
                widget.enable(self.show_animations)

    def disable_id(self, id):
        for widget in self.widgets:
            if widget.enabled and widget.id == id:
                widget.disable(self.show_animations)

    def switch_theme(self, theme_name):
        if (self.theme.name != theme_name):
            self.theme = HeadUpDisplayTheme(theme_name)            
            for widget in self.widgets:
                widget.set_theme(self.theme, self.show_animations)
            
            self.preferences.persist_preferences({'theme_name': theme_name})
        
    def start_setup_id(self, id, setup_type):
        for widget in self.widgets:
            if widget.enabled and widget.id == id:
                widget.start_setup(setup_type)
                
    # Check if the widgets are finished unloading, then disable the poller
    # This should only run when we have a state poller
    def disable_poller_check(self):
        enabled = False
        for widget in self.widgets:
            if not widget.cleared:
                enabled = True
                break
        
        if not enabled:
            if self.poller:
                self.poller.disable()
            
            if self.disable_poller_job is not None:
                cron.cancel(self.disable_poller_job)
                self.disable_poller_job = None
        
    def content_update(self, data):
        for widget in self.widgets:
            update_dict = {}
            for key in data:
                if key in widget.subscribed_content:
                    update_dict[key] = data[key]
                    
            if len(update_dict) > 0:
                widget.update_content(update_dict, self.show_animations)
                
    def log_update(self, logs):
        new_log = logs[-1]
        for widget in self.widgets:
            if new_log['type'] in widget.subscribed_logs or '*' in widget.subscribed_logs:
                widget.append_log(new_log, self.show_animations)
                
    # Send mouse events to enabled widgets
    def poll_mouse_pos(self):
        pos = ctrl.mouse_pos()
        
        if (self.prev_mouse_pos is None or numpy.linalg.norm(numpy.array(pos) - numpy.array(self.prev_mouse_pos)) > 1):
            self.prev_mouse_pos = pos
            for widget in self.widgets:
                if widget.enabled:
                    widget.mouse_move(self.prev_mouse_pos)


def create_hud():
    global hud
    preferences = HeadUpDisplayUserPreferences()
    
    from user.talon_hud.knausj_bindings import KnausjStatePoller    
    poller = KnausjStatePoller()
    hud = HeadUpDisplay(hud_content, preferences, poller)

app.register('ready', create_hud)

@mod.action_class
class Actions:
                
    def enable_hud():
        """Enables the HUD"""
        global hud
        hud.enable()
        
    def disable_hud():
        """Disables the HUD"""
        global hud
        hud.disable()
        
    def add_hud_log(type: str, message: str):
        """Disables the HUD"""
        global hud_content
        hud_content.append_to_log(type, message)
        
    def enable_hud_id(id: str):
        """Enables a specific hud element"""
        hud.enable_id(id)
        
    def disable_hud_id(id: str):
        """Disables a specific hud element"""
        hud.disable_id(id)
        
    def switch_hud_theme(theme_name: str):
        """Switches the UI theme"""
        global hud
        hud.switch_theme(theme_name)
        
    def set_hud_setup_mode(setup_mode: str):
        """Starts a setup mode which can change position"""
        global hud
        hud.start_setup_id('status_bar', setup_mode)
