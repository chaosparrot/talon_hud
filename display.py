from talon import Context, Module, actions, app, skia, cron, ctrl, scope, canvas, registry, settings, ui, speech_system
import os
import time
import numpy

from typing import Any
from user.talon_hud.preferences import HeadUpDisplayUserPreferences
from user.talon_hud.theme import HeadUpDisplayTheme
from user.talon_hud.content.state import hud_content
from user.talon_hud.content.status_bar_poller import StatusBarPoller
from user.talon_hud.content.history_poller import HistoryPoller
from user.talon_hud.layout_widget import LayoutWidget
from user.talon_hud.widgets.statusbar import HeadUpStatusBar
from user.talon_hud.widgets.eventlog import HeadUpEventLog
from user.talon_hud.widgets.abilitybar import HeadUpAbilityBar
from user.talon_hud.widgets.textbox import HeadUpTextBox
from user.talon_hud.widgets.choicepanel import HeadUpChoicePanel
from user.talon_hud.widgets.documentationpanel import HeadUpDocumentationPanel
from user.talon_hud.widgets.contextmenu import HeadUpContextMenu
from user.talon_hud.content.typing import HudPanelContent, HudButton
from user.talon_hud.content.poller import Poller
from user.talon_hud.utils import string_to_speakable_string

# Taken from knausj/code/numbers to make Talon HUD standalone
# The numbers should realistically stay very low for choices, because you dont want choice overload for the user, up to 100
digits = "zero one two three four five six seven eight nine".split()
teens = "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
tens = "twenty thirty forty fifty sixty seventy eighty ninety".split()
digits_without_zero = digits[1:]
numerical_choice_strings = []
numerical_choice_strings.extend(digits_without_zero)
numerical_choice_strings.extend(teens)
for index, ten in enumerate(tens):
    numerical_choice_strings.append(ten)
    for digit in digits_without_zero:
       numerical_choice_strings.append(ten + " " + digit)
numerical_choice_strings.append("hundred")

ctx = Context()
mod = Module()
mod.list("talon_hud_widget_names", desc="List of available widgets by name linked to their identifier")
mod.list("talon_hud_widget_options", desc="List of options available to the widgets")
mod.list("talon_hud_choices", desc="Available choices shown on screen")
mod.list("talon_hud_numerical_choices", desc="Available choices shown on screen numbered")
mod.list("talon_hud_quick_choices", desc="List of widgets with their quick options")
mod.tag("talon_hud_available", desc="Tag that shows the availability of the Talon HUD repository for other scripts")
mod.tag("talon_hud_visible", desc="Tag that shows that the Talon HUD is visible")
mod.tag("talon_hud_choices_visible", desc="Tag that shows there are choices available on screen that can be chosen")

ctx.tags = ['user.talon_hud_available']

class HeadUpDisplay:
    enabled = False
    display_state = None
    preferences = None
    theme = None
    pollers = []
    keep_alive_pollers = [] # These pollers will only deactivate when the hud deactivates    
    disable_poller_job = None
    show_animations = False
    widgets = []
    choices_visible = False
    
    prev_mouse_pos = None
    mouse_poller = None
    
    def __init__(self, display_state, preferences):
        self.display_state = display_state
        self.preferences = preferences
        self.pollers = {}
        self.disable_poller_job = None
        self.theme = HeadUpDisplayTheme(self.preferences.prefs['theme_name'])
        self.show_animations = self.preferences.prefs['show_animations']
        self.widgets = [
            HeadUpStatusBar('status_bar', self.preferences.prefs, self.theme),
            HeadUpEventLog('event_log', self.preferences.prefs, self.theme),
            HeadUpTextBox('Text box', self.preferences.prefs, self.theme, {'topics': ['*']}),
            HeadUpDocumentationPanel('Documentation', self.preferences.prefs, self.theme, {'topics': ['documentation']}),            
            # Extra text boxes can be defined to be assigned to different topics
            # HeadUpTextBox('Text box two', self.preferences.prefs, self.theme, {'topics': ['your_topic_here'], 'current_topic': 'your_topic_here'}),
            HeadUpChoicePanel('Choices', self.preferences.prefs, self.theme, {'topics': ['choice'], 'current_topic': 'choice'}),

            # Special widgets that have varying positions
            HeadUpContextMenu('context_menu', self.preferences.prefs, self.theme),
        ]
        
        # These pollers should always be active and available when reloading Talon HUD
        self.pollers = {
            'status': StatusBarPoller(),
            'history': HistoryPoller()
        }
        self.keep_alive_pollers = ['status', 'history']
        
        # Uncomment the line below to add language icons
        # self.subscribe_content_id('status_bar', 'language')
        
    def start(self):
        if (self.preferences.prefs['enabled']):
            self.enable()    	
            
    def enable(self, persisted=False):
        if not self.enabled:
            self.enabled = True
            
            attached_topics = list(self.keep_alive_pollers)
            for widget in self.widgets:
                if widget.preferences.enabled and not widget.enabled:
                    widget.enable()
                    if widget.topic:
                    	attached_topics.append(widget.topic)

            for topic, poller in self.pollers.items():
            	if topic in attached_topics:
                    poller.enable()
            
            self.display_state.register('content_update', self.content_update)
            self.display_state.register('panel_update', self.panel_update)            
            self.display_state.register('log_update', self.log_update)
            self.determine_active_setup_mouse()            
            if persisted:
                self.preferences.persist_preferences({'enabled': True})
            self.update_context()

    def disable(self, persisted=False):
        if self.enabled:
            self.enabled = False
            
            for widget in self.widgets:
                if widget.enabled:
                    widget.disable()
            
            self.disable_poller_job = cron.interval('30ms', self.disable_poller_check)
            self.display_state.unregister('content_update', self.content_update)
            self.display_state.unregister('panel_update', self.panel_update)
            self.display_state.unregister('log_update', self.log_update)
            self.determine_active_setup_mouse()
            
            if persisted:
                self.preferences.persist_preferences({'enabled': False})
            self.update_context()
            
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
                if widget.topic in self.pollers and not self.pollers[widget.topic].enabled:
                	self.pollers[widget.topic].enable()                

    def disable_id(self, id):
        for widget in self.widgets:
            if widget.enabled and widget.id == id:
                widget.disable(True)
                if widget.topic in self.pollers and widget.topic not in self.keep_alive_pollers:
                	self.pollers[widget.topic].disable()
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
    
    def register_poller(self, topic: str, poller: Poller, keep_alive: bool):
        self.remove_poller(topic)
        self.pollers[topic] = poller
        
        # Keep the poller alive even if no widgets have subscribed to its topic
        if keep_alive and not self.pollers[topic].enabled:
            self.keep_alive_pollers.append(topic)
            self.pollers[topic].enable()
        # Automatically enable the poller if it was active on restart        
        else:
            for widget in self.widgets:
                if widget.topic == topic:
                    self.pollers[topic].enable()
                    break
        
    def remove_poller(self, topic: str):
        if topic in self.pollers:
            self.pollers[topic].disable()
            del self.pollers[topic]
    
    def activate_poller(self, topic: str):
        # Find the widget we need to claim for this topic
        # Prioritizing specific widgets over the fallback one
        widget_to_claim = None
        using_fallback = True
        if topic not in self.keep_alive_pollers:
            for widget in self.widgets:
                if topic in widget.subscribed_topics or ('*' in widget.subscribed_topics and using_fallback):
                    widget_to_claim = widget
                    if topic in widget.subscribed_topics:
                   	    using_fallback = False
        
        # Deactivate the topic connected to the widget
        if widget_to_claim:
            if widget_to_claim.topic in self.pollers and widget_to_claim.topic not in self.keep_alive_pollers:
                self.pollers[widget_to_claim.topic].disable()
            widget_to_claim.set_topic(topic)
    	
    	# Enable the poller afterwards
        if topic in self.pollers and not self.pollers[topic].enabled:
            self.pollers[topic].enable()
		
         
    # Check if the widgets are finished unloading, then disable the poller
    # This should only run when we have a state poller
    def disable_poller_check(self):
        enabled = False
        for widget in self.widgets:
            if not widget.cleared:
                enabled = True
                break
        
        if not enabled:
            for topic, poller in self.pollers.items():
                poller.disable()
            cron.cancel(self.disable_poller_job)
            self.disable_poller_job = None
        
    def content_update(self, data):
        for widget in self.widgets:
            update_dict = {}
            for key in data:
                if key in widget.subscribed_content:
                    update_dict[key] = data[key]
                    
            if len(update_dict) > 0:
                current_enabled_state = widget.enabled
                widget.update_content(update_dict)
                
                # If the enabled state has changed because of a content update like a sleep command
                # Do appropriate poller enabling / disabling
                if widget.enabled != current_enabled_state:
                    if widget.topic in self.pollers and widget.topic not in self.keep_alive_pollers:
                        if widget.enabled: 
                            self.pollers[widget.topic].enable()
                        else:
                            self.pollers[widget.topic].disable()
                
    def log_update(self, logs):
        new_log = logs[-1]
        for widget in self.widgets:
            if new_log['type'] in widget.subscribed_logs or '*' in widget.subscribed_logs:
                widget.append_log(new_log)

    def panel_update(self, panel_content: HudPanelContent):
        updated = False
        widget_to_claim = None
        using_fallback = True
        topic = panel_content.topic
        
        # Do not force a reopen of Talon HUD without explicit user permission
        if not self.enabled:
            panel_content.show = False
        
        # Find the widget to use for updating
        # Prefer the widget that is already registered 
        # Then widgets that have a topic subscribed
        # And lastly the fallback widget
        if topic not in self.keep_alive_pollers:
            for widget in self.widgets:
                if topic in widget.subscribed_topics or ('*' in widget.subscribed_topics and using_fallback):
                    if topic == widget.topic:
                        widget_to_claim = widget
                        break
                    else:
                        widget_to_claim = widget
                        if topic in widget.subscribed_topics:
                            using_fallback = False
        

        if widget_to_claim:
			# When a new topic is published it can lay claim to a widget
            # So old pollers need to be deregistered in that case
            current_topic = widget_to_claim.topic                
            updated = widget_to_claim.update_panel(panel_content)
            if updated and current_topic != widget_to_claim.topic:
                if current_topic in self.pollers and current_topic not in self.keep_alive_pollers:
                    self.pollers[widget_to_claim.topic].disable()
            
        if updated:
            self.update_context()

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

    # Increase the page number by one on the widget if it is enabled
    def increase_widget_page(self, widget_id: str):
        for widget in self.widgets:
            if widget.enabled and widget.id == widget_id and isinstance(widget, LayoutWidget):
                widget.set_page_index(widget.page_index + 1)

    # Decrease the page number by one on the widget if it is enabled
    def decrease_widget_page(self, widget_id: str):
        for widget in self.widgets:
            if widget.enabled and widget.id == widget_id and isinstance(widget, LayoutWidget):
                widget.set_page_index(widget.page_index - 1)

    # Move the context menu over to the given location fitting within the screen
    def move_context_menu(self, widget_id: str, pos_x: int, pos_y: int, buttons: list[HudButton]):
        connected_widget = None
        context_menu_widget = None
        for widget in self.widgets:
            if widget.enabled and widget.id == widget_id:
                connected_widget = widget
            elif widget.id == 'context_menu':      
                context_menu_widget = widget
        if connected_widget and context_menu_widget:
            context_menu_widget.connect_widget(connected_widget, pos_x, pos_y, buttons)
            self.choices_visible = True
            self.update_context()
            
    # Connect the context menu using voice
    def connect_context_menu(self, widget_id):
        connected_widget = None
        context_menu_widget = None
        for widget in self.widgets:
            if widget.enabled and widget.id == widget_id:
                connected_widget = widget
            elif widget.id == 'context_menu':      
                context_menu_widget = widget
        
        buttons = []
        if connected_widget:
            pos_x = connected_widget.x + connected_widget.width / 2
            pos_y = connected_widget.y + connected_widget.height
            buttons = connected_widget.buttons
        
            if context_menu_widget:
                context_menu_widget.connect_widget(connected_widget, pos_x, pos_y, buttons)
                self.choices_visible = True
                self.update_context()                
    
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
            self.choices_visible = False
            self.update_context()
    
    # Active a given choice for a given widget
    def activate_choice(self, choice_string):
        widget_id, choice_index = choice_string.split("|")
        for widget in self.widgets:
            if widget.id == widget_id:
                if isinstance(widget, HeadUpChoicePanel):
                    widget.select_choice(int(choice_index))
                    self.update_context()
                else:
                    widget.click_button(int(choice_index))

    # Updates the context based on the current HUD state
    def update_context(self):
        tags = [
            'user.talon_hud_available'
        ]
        
        widget_names = {}
        choices = {}
        quick_choices = {}
        numerical_choices = {}
        for widget in self.widgets:
            current_widget_names = [string_to_speakable_string(widget.id)]        
            if isinstance(widget, HeadUpTextBox):
                content_title = string_to_speakable_string(widget.panel_content.title)
                if content_title:
                    current_widget_names.append(string_to_speakable_string(widget.panel_content.title))
                    
            for widget_name in current_widget_names:
                widget_names[widget_name] = widget.id
                
            # Add quick choices
            for index, button in enumerate(widget.buttons):
                choice_title = string_to_speakable_string(button.text)                    
                if choice_title:
                    for widget_name in current_widget_names:
                        quick_choices[widget_name + " " + choice_title] = widget.id + "|" + str(index)
            
            # Add context choices
            if widget.enabled and isinstance(widget, HeadUpContextMenu):
                for index, button in enumerate(widget.buttons):
                    choice_title = string_to_speakable_string(button.text)
                    if choice_title:
                        choices[choice_title] = widget.id + "|" + str(index)
             
            # Add choice panel choices
            if widget.enabled and isinstance(widget, HeadUpChoicePanel):
                self.choices_visible = True
                for index, choice in enumerate(widget.choices):
                    choice_title = string_to_speakable_string(choice.text)
                    if choice_title:
                        choices[choice_title] = widget.id + "|" + str(index)
                    numerical_choices[numerical_choice_strings[index]] = widget.id + "|" + str(index)
                        
                if widget.panel_content.choices and widget.panel_content.choices.multiple:
                    choices["confirm"] = widget.id + "|" + str(index + 1)

        if self.enabled:
            tags.append('user.talon_hud_visible')
        if self.choices_visible:
            tags.append('user.talon_hud_choices_visible')
        ctx.tags = tags
        ctx.lists['user.talon_hud_numerical_choices'] = numerical_choices
        ctx.lists['user.talon_hud_widget_names'] = widget_names
        ctx.lists['user.talon_hud_choices'] = choices
        ctx.lists['user.talon_hud_quick_choices'] = quick_choices
    

preferences = HeadUpDisplayUserPreferences()
hud = HeadUpDisplay(hud_content, preferences)

def hud_enable():
    global hud
    hud.start()

app.register('ready', hud_enable)

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
                
    def show_context_menu(widget_id: str, pos_x: int, pos_y: int, buttons: list[HudButton]):
        """Show the context menu for a specific widget id"""
        hud.move_context_menu(widget_id, pos_x, pos_y, buttons)
        
    def hide_context_menu():
        """Show the context menu for a specific widget id"""
        hud.hide_context_menu()
        
    def increase_widget_page(widget_id: str):
        """Increase the content page of the widget if it has pages available"""
        global hud
        hud.increase_widget_page(widget_id)

    def decrease_widget_page(widget_id: str):
        """Decrease the content page of the widget if it has pages available"""
        global hud
        hud.decrease_widget_page(widget_id)
        
    def decrease_widget_page(widget_id: str):
        """Decrease the content page of the widget if it has pages available"""
        global hud
        hud.decrease_widget_page(widget_id)
        
    def hud_widget_options(widget_id: str):
        """Connect the widget to the context menu to show the options"""
        global hud
        hud.connect_context_menu(widget_id)
        
    def hud_activate_choice(choice_string: str):
        """Activate a choice available on the screen"""    
        global hud
        hud.activate_choice(choice_string)
        
    def hud_activate_choices(choice_string_list: list[str]):
        """Activate multiple choices available on the screen"""    
        global hud
        for choice_string in choice_string_list:
            hud.activate_choice(choice_string)
        
    def hud_add_poller(topic: str, poller: Poller, keep_alive: bool = False):
        """Add a content poller / listener to the HUD"""    
        global hud
        hud.register_poller(topic, poller, keep_alive)
        
    def hud_activate_poller(topic: str):
        """Enables a poller and claims a widget"""    
        global hud
        hud.activate_poller(topic)
