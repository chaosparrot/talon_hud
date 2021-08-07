from talon import Context, Module, actions, app, skia, cron, ctrl, scope, canvas, registry, settings, ui, speech_system
import os
import time
import numpy

from typing import Any
from user.talon_hud.preferences import HeadUpDisplayUserPreferences
from user.talon_hud.theme import HeadUpDisplayTheme
from user.talon_hud.state import hud_content
from user.talon_hud.widgets.statusbar import HeadUpStatusBar
from user.talon_hud.widgets.eventlog import HeadUpEventLog
from user.talon_hud.widgets.abilitybar import HeadUpAbilityBar
from user.talon_hud.widgets.textbox import HeadUpTextBox
from user.talon_hud.widgets.contextmenu import HeadUpContextMenu
from user.talon_hud.content_types import HudPanelContent, HudButton

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
            HeadUpStatusBar('status_bar', self.preferences.prefs, self.theme),
            HeadUpEventLog('event_log', self.preferences.prefs, self.theme),
            #HeadUpAbilityBar('ability_bar', self.preferences.prefs, self.theme),
            HeadUpTextBox('debug_panel', self.preferences.prefs, self.theme, {'topics': ['debug']}),
            
            # Special widgets that have varying positions
            HeadUpContextMenu('context_menu', self.preferences.prefs, self.theme),            
        ]
        
        # Uncomment the line below to add language icons
        # self.subscribe_content_id('status_bar', 'language')
        
        if (self.preferences.prefs['enabled']):
            self.enable()
            
    def enable(self, persisted=False):
        if not self.enabled:
            self.enabled = True
            if self.poller:
                self.poller.enable()
                
            for widget in self.widgets:
                if widget.preferences.enabled and not widget.enabled:
                    widget.enable()
            
            self.display_state.register('content_update', self.content_update)
            self.display_state.register('panel_update', self.panel_update)            
            self.display_state.register('log_update', self.log_update)
            self.determine_active_setup_mouse()            
            if persisted:
                self.preferences.persist_preferences({'enabled': True})

    def disable(self, persisted=False):
        if self.enabled:
            self.enabled = False
            
            for widget in self.widgets:
                if widget.enabled:
                    widget.disable()
            
            if self.poller:
                self.disable_poller_job = cron.interval('30ms', self.disable_poller_check)                
            
            self.display_state.unregister('content_update', self.content_update)
            self.display_state.unregister('panel_update', self.panel_update)
            self.display_state.unregister('log_update', self.log_update)
            self.determine_active_setup_mouse()
            
            if persisted:
                self.preferences.persist_preferences({'enabled': False})
        
    # Persist the preferences of all the widgets
    def persist_widgets_preferences(self):
        dict = {}
        for widget in self.widgets:
            if widget.preferences.mark_changed:
                dict = {**dict, **widget.preferences.export(widget.id)}
                widget.preferences.mark_changed = False
        self.preferences.persist_preferences(dict)
        self.determine_active_setup_mouse()        
    
    def enable_id(self, id):
        if not self.enabled:
            self.enable()
    
        for widget in self.widgets:
            if not widget.enabled and widget.id == id:
                widget.enable(True)

    def disable_id(self, id):
        for widget in self.widgets:
            if widget.enabled and widget.id == id:
                widget.disable(True)
        self.determine_active_setup_mouse()
        
    def subscribe_content_id(self, id, content_key):
        for widget in self.widgets:
            if widget.id == id:
                if content_key not in widget.subscribed_content:
                    widget.subscribed_content.append(content_key)

    def set_widget_preference(self, id, property, value, persisted=False):
        for widget in self.widgets:
            if widget.id == id:
                widget.set_preference(property, value, persisted)
        self.determine_active_setup_mouse()

    def switch_theme(self, theme_name):
        if (self.theme.name != theme_name):
            self.theme = HeadUpDisplayTheme(theme_name)
            for widget in self.widgets:
                widget.set_theme(self.theme)
            
            self.preferences.persist_preferences({'theme_name': theme_name})
        
    def start_setup_id(self, setup_type, id = "*"):
        for widget in self.widgets:
            if widget.enabled and ( id == "*" or widget.id == id ) and widget.setup_type != setup_type:
                widget.start_setup(setup_type)
                
        self.determine_active_setup_mouse()
                
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
                cron.cancel(self.disable_poller_job)
                self.disable_poller_job = None
        
    def content_update(self, data):
        for widget in self.widgets:
            update_dict = {}
            for key in data:
                if key in widget.subscribed_content:
                    update_dict[key] = data[key]
                    
            if len(update_dict) > 0:
                widget.update_content(update_dict)
                
    def log_update(self, logs):
        new_log = logs[-1]
        for widget in self.widgets:
            if new_log['type'] in widget.subscribed_logs or '*' in widget.subscribed_logs:
                widget.append_log(new_log)

    def panel_update(self, data):
        for widget in self.widgets:
            panel_content = None        
            for key in data:
                if key in widget.subscribed_topics:
                    if panel_content == None or data[key].published_at > panel_content.published_at:
                        panel_content = data[key]
            
            if panel_content != None:
                widget.update_panel(panel_content)

    # Determine whether or not we need to have a global mouse poller
    # This poller is needed for setup modes as not all canvases block the mouse
    def determine_active_setup_mouse(self):
        has_setup_modes = False
        for widget in self.widgets:
            if (widget.setup_type not in ["", "mouse_drag"]):
                has_setup_modes = True
                break
    
        if has_setup_modes and not self.mouse_poller:
            self.mouse_poller = cron.interval('16ms', self.poll_mouse_pos_for_setup)
        if not has_setup_modes and self.mouse_poller:
            cron.cancel(self.mouse_poller)
            self.mouse_poller = None

    # Send mouse events to enabled widgets that have an active setup going on
    def poll_mouse_pos_for_setup(self):
        pos = ctrl.mouse_pos()
        
        if (self.prev_mouse_pos is None or numpy.linalg.norm(numpy.array(pos) - numpy.array(self.prev_mouse_pos)) > 1):
            self.prev_mouse_pos = pos
            for widget in self.widgets:
                if widget.enabled and widget.setup_type != "":
                    widget.setup_move(self.prev_mouse_pos)

    # Move the context menu over to the given location fitting within the screen
    def move_context_menu(self, widget_id: str, pos_x: int, pos_y: int, buttons: Any):
        connected_widget = None
        context_menu_widget = None
        for widget in self.widgets:
            if widget.enabled and widget.id == widget_id:
                connected_widget = widget
            elif widget.id == 'context_menu':      
                context_menu_widget = widget
        if connected_widget and context_menu_widget:
            context_menu_widget.connect_widget(connected_widget, pos_x, pos_y, buttons)
    
    # Hide the context menu
    # Generally you want to do this when you click outside of the menu itself
    def hide_context_menu(self):
        context_menu_widget = None    
        for widget in self.widgets:
            if widget.id == 'context_menu' and widget.enabled:      
                context_menu_widget = widget
                break
        if context_menu_widget:
            context_menu_widget.disconnect_widget()        

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
        hud.enable(True)

    def disable_hud():
        """Disables the HUD"""
        global hud
        hud.disable(True)

    def persist_hud_preferences():
        """Saves the HUDs preferences"""
        global hud
        hud.persist_widgets_preferences()

    def enable_hud_id(id: str):
        """Enables a specific hud element"""
        global hud        
        hud.enable_id(id)
        
    def set_widget_preference(id: str, property: str, value: Any):
        """Set a specific widget preference"""
        hud.set_widget_preference(id, property, value, True)
        
    def disable_hud_id(id: str):
        """Disables a specific hud element"""
        global hud
        hud.disable_id(id)
        
    def switch_hud_theme(theme_name: str):
        """Switches the UI theme"""
        global hud
        hud.switch_theme(theme_name)
        
    def set_hud_setup_mode(setup_mode: str, id: str):
        """Starts a setup mode which can change position"""
        global hud
        hud.start_setup_id(id, setup_mode)
                
    def show_context_menu(widget_id: str, pos_x: int, pos_y: int, buttons: Any):
        """Show the context menu for a specific widget id"""
        hud.move_context_menu(widget_id, pos_x, pos_y, buttons)
        
    def hide_context_menu():
        """Show the context menu for a specific widget id"""
        hud.hide_context_menu()
        
    # - Content related actions
    
    def add_hud_log(type: str, message: str):
        """Disables the HUD"""
        global hud_content
        hud_content.append_to_log(type, message)

    def add_status_icon(id: str, image: str, explanation: str):
        """Add an icon to the status bar"""
        global hud_content
        hud_content.add_to_set("status_icons", {
            "id": id,
            "image": image,
            "explanation": "",
            "clickable": False
        })

    def remove_status_icon(id: str):
        """Remove an icon to the status bar"""
        global hud_content
        hud_content.remove_from_set("status_icons", {
            "id": id
        })

    def add_hud_ability(id: str, image: str, colour: str, enabled: bool, activated: bool):
        """Add a hud ability or update it"""
        global hud_content
        hud_content.add_to_set("abilities", {
            "id": id,
            "image": image,
            "colour": colour,
            "enabled": enabled,
            "activated": 5 if activated else 0
        })

    def remove_hud_ability(id: str):
        """Remove an ability"""
        global hud_content
        hud_content.remove_from_set("abilities", {
            "id": id
        })    
        
    def hud_publish_content(content: str, widget_hint: str = '', title:str = '', show:bool = True, buttons: list[HudButton] = None):
        """Publish a specific piece of content to a user defined widget"""            
        if buttons == None:
            buttons = []
        content = HudPanelContent(widget_hint, title, [content], buttons, time.time(), show)
        
        global hud_content
        hud_content.publish(content)
        