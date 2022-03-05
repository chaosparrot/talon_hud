from talon import Context, Module, actions, app, skia, cron, ctrl, scope, canvas, registry, settings, ui, fs
from talon.types.point import Point2d
import os
import time
import numpy

from typing import Any, Union
from .preferences import HeadUpDisplayUserPreferences
from .theme import HeadUpDisplayTheme
from .event_dispatch import HeadUpEventDispatch
from .widget_manager import HeadUpWidgetManager
from .content.content_builder import HudContentBuilder
from .content.state import hud_content
from .layout_widget import LayoutWidget
from .widgets.textpanel import HeadUpTextPanel
from .widgets.choicepanel import HeadUpChoicePanel
from .widgets.contextmenu import HeadUpContextMenu
from .content.typing import HudPanelContent, HudButton, HudContentEvent, HudContentPage
from .content.poller import Poller
from .utils import string_to_speakable_string


# Taken from knausj/code/numbers to make Talon HUD standalone
# The numbers should realistically stay very low for choices, because you don't want choice overload for the user, up to 100
digits = "zero one two three four five six seven eight nine".split()
teens = "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
tens = "twenty thirty forty fifty sixty seventy eighty ninety".split()
digits_without_zero = digits[1:]
numerical_choice_index_map = {}
numerical_choice_strings = []
numerical_choice_strings.extend(digits_without_zero)
numerical_choice_strings.extend(teens)
for digit_index, digit in enumerate(digits):
    numerical_choice_index_map[digit] = digit_index
for digit_index, digit_plus_ten in enumerate(teens):
    numerical_choice_index_map[digit_plus_ten] = digit_index + 10

for index, ten in enumerate(tens):
    numerical_choice_strings.append(ten)
    numerical_choice_index_map[ten] = (index + 1) * 10 + 10
    for digit_index, digit in enumerate(digits_without_zero):
       numerical_choice_strings.append(ten + " " + digit)
       numerical_choice_index_map[ten + " " + digit] = ( index + 1 ) * 10 + digit_index + 1
    
numerical_choice_strings.append("one hundred")
numerical_choice_index_map["one hundred"] = 100

ctx = Context()
mod = Module()
mod.list("talon_hud_widget_names", desc="List of available widgets by name linked to their identifier")
mod.list("talon_hud_widget_options", desc="List of options available to the widgets")
mod.list("talon_hud_choices", desc="Available choices shown on screen")
mod.list("talon_hud_themes", desc="Available themes for the Talon HUD")
mod.list("talon_hud_numerical_choices", desc="Available choices shown on screen numbered")
mod.list("talon_hud_quick_choices", desc="List of widgets with their quick options")
mod.list("talon_hud_widget_enabled_voice_commands", desc="List of extra voice commands added by visible widgets")
mod.tag("talon_hud_available", desc="Tag that shows the availability of the Talon HUD repository for other scripts")
mod.tag("talon_hud_visible", desc="Tag that shows that the Talon HUD is visible")
mod.tag("talon_hud_choices_visible", desc="Tag that shows there are choices available on screen that can be chosen")
mod.setting("talon_hud_environment", type="string", desc="Which environment to set the HUD in - Useful for setting up a HUD for screen recording or other tasks")

ctx.tags = ["user.talon_hud_available"]
ctx.settings["user.talon_hud_environment"] = ""
ctx.lists["user.talon_hud_widget_enabled_voice_commands"] = []

# A list of Talon HUD versions that can be used to check for in other packages
TALON_HUD_RELEASE_030 = 3 # Walk through version
TALON_HUD_RELEASE_040 = 4 # Multi-monitor version
TALON_HUD_RELEASE_050 = 5 # Debugging / screen overlay release
TALON_HUD_RELEASE_060 = 6 # Persistent content release
CURRENT_TALON_HUD_VERSION = TALON_HUD_RELEASE_060

@mod.scope
def scope():
    return {"talon_hud_version": CURRENT_TALON_HUD_VERSION}

class HeadUpDisplay:
    enabled = False
    display_state = None
    preferences = None
    theme = None
    event_dispatch = None
    pollers = []
    keep_alive_pollers = [] # These pollers will only deactivate when the hud deactivates    
    custom_themes = {}
    disable_poller_job = None
    show_animations = False
    choices_visible = False
    allowed_content_operations = ["*"]
    
    prev_mouse_pos = None
    mouse_poller = None
    current_talon_hud_environment = ""

    enabled_voice_commands = {}
    update_preferences_debouncer = None
    update_context_debouncer = None
    update_cue_context_debouncer = None
    update_environment_debouncer = None
    
    watching_directories = False
    
    def __init__(self, display_state, preferences):
        self.display_state = display_state
        self.preferences = preferences
        self.pollers = {}
        self.keep_alive_pollers = []
        self.disable_poller_job = None
        self.theme = HeadUpDisplayTheme(self.preferences.prefs["theme_name"])
        self.event_dispatch = HeadUpEventDispatch()
        self.show_animations = self.preferences.prefs["show_animations"]
        self.widget_manager = HeadUpWidgetManager(self.preferences, self.theme, self.event_dispatch)

        self.display_state.register("broadcast_update", self.broadcast_update)

    def start(self):
        if (self.preferences.prefs["enabled"]):
            # Temporarily disable broadcast updates that were captured with the previous handler in the init
            self.display_state.unregister("broadcast_update", self.broadcast_update)        
            self.enable()
            ctx.tags = ["user.talon_hud_available", "user.talon_hud_visible", "user.talon_hud_choices_visible"]

            if actions.sound.active_microphone() == "None":
                actions.user.hud_add_log("warning", "Microphone is set to \"None\"!\n\nNo voice commands will be registered.")
    
    def enable(self, persisted=False):
        if not self.enabled:
            self.enabled = True
            self.display_state.register("broadcast_update", self.broadcast_update)            

            # Only reset the talon HUD environment after a user action
            # And only set the visible tag
            if persisted:
                ctx.tags = ["user.talon_hud_available", "user.talon_hud_visible", "user.talon_hud_choices_visible"]
                self.current_talon_hud_environment = settings.get("user.talon_hud_environment")
            
            # Connect the events relating to non-content communication
            self.event_dispatch.register("persist_preferences", self.debounce_widget_preferences)
            self.event_dispatch.register("hide_context_menu", self.hide_context_menu)
            self.event_dispatch.register("deactivate_poller", self.deactivate_poller)
            self.event_dispatch.register("show_context_menu", self.move_context_menu)
            self.event_dispatch.register("synchronize_poller", self.synchronize_widget_poller)

            for widget in self.widget_manager.widgets:
                if widget.preferences.enabled and not widget.enabled:
                    widget.enable()
            self.synchronize_pollers()

            # Reload the preferences just in case a screen change happened in between the hidden state
            if persisted:
                self.reload_preferences()
            
            ui.register("screen_change", self.reload_preferences)
            settings.register("user.talon_hud_environment", self.hud_environment_change)
            self.determine_active_setup_mouse()
            if persisted:
                self.preferences.persist_preferences({"enabled": True})

            # Make sure context isn't updated in this thread because of automatic reloads
            cron.cancel(self.update_context_debouncer)
            self.update_context_debouncer = cron.after("50ms", self.update_context)

    def disable(self, persisted=False):
        if self.enabled:
            self.enabled = False            
            
            for widget in self.widget_manager.widgets:
                if widget.enabled:
                    widget.disable()
            self.synchronize_pollers()
            
            # Disconnect the events relating to non-content communication
            self.event_dispatch.unregister("persist_preferences", self.debounce_widget_preferences)
            self.event_dispatch.unregister("hide_context_menu", self.hide_context_menu)
            self.event_dispatch.unregister("deactivate_poller", self.deactivate_poller)
            self.event_dispatch.unregister("show_context_menu", self.move_context_menu)
            self.event_dispatch.unregister("synchronize_poller", self.synchronize_widget_poller)
            
            self.disable_poller_job = cron.interval("30ms", self.disable_poller_check)
            self.display_state.unregister("broadcast_update", self.broadcast_update)
            ui.unregister("screen_change", self.reload_preferences)
            settings.unregister("user.talon_hud_environment", self.hud_environment_change)            
            self.determine_active_setup_mouse()
            
            # Only change the tags upon a user action - No automatic flow should set tags to prevent cascades
            if persisted:
                ctx.tags = ["user.talon_hud_available"]
                self.preferences.persist_preferences({"enabled": False})
                
            # Make sure context isn't updated in this thread because of automatic reloads
            cron.cancel(self.update_context_debouncer)
            self.update_context_debouncer = cron.after("50ms", self.update_context)
            
    # Persist the preferences of all the widgets
    def persist_widgets_preferences(self, _ = None):
        dict = {}
        for widget in self.widget_manager.widgets:
            if widget.preferences.mark_changed:
                dict = {**dict, **widget.preferences.export(widget.id)}
                widget.preferences.mark_changed = False
                
        self.preferences.persist_preferences(dict)
        self.determine_active_setup_mouse()
        
    # Debounce the widget preference persistence to make sure we do not get a ton of persisting operations
    def debounce_widget_preferences(self, _ = None):
        cron.cancel(self.update_preferences_debouncer)
        self.update_preferences_debouncer = cron.after("100ms", self.persist_widgets_preferences)
    
    def enable_id(self, id):
        if not self.enabled:
            self.enable()
    
        for widget in self.widget_manager.widgets:
            if not widget.enabled and widget.id == id:
                widget.enable(True)                
                for topic, poller in self.pollers.items():
                    if topic in widget.current_topics and (not hasattr(self.pollers[topic], "enabled") or not self.pollers[topic].enabled):
                        self.pollers[topic].enable()

                self.update_context()
                break
                
    def disable_id(self, id):
        for widget in self.widget_manager.widgets:
            if widget.enabled and widget.id == id:
                widget.disable(True)
                self.synchronize_widget_poller(widget.id)
                self.update_context()
                break
        self.determine_active_setup_mouse()
        
    def subscribe_content_id(self, id, content_key):
        for widget in self.widget_manager.widgets:
            if widget.id == id:
                if content_key not in widget.subscribed_content:
                    widget.subscribed_content.append(content_key)
                    
    def unsubscribe_content_id(self, id, content_key):
        for widget in self.widget_manager.widgets:
            if widget.id == id:
                if content_key in widget.subscribed_content:
                    widget.subscribed_content.remove(content_key)

    def set_widget_preference(self, id, property, value, persisted=False):
        for widget in self.widget_manager.widgets:
            if widget.id == id:
                widget.set_preference(property, value, persisted)
        self.determine_active_setup_mouse()

    def add_theme(self, theme_name, theme_dir):
        if os.path.exists(theme_dir):
            self.custom_themes[theme_name] = theme_dir
        else:
            app.notify("Invalid directory for '" + theme_name + "': " + theme_dir)

    def switch_theme(self, theme_name, disable_animation = False, forced = False):
        if self.theme.name != theme_name or forced:
            should_reset_watch = self.watching_directories
            if should_reset_watch:
                self.unwatch_directories()
            
            theme_dir = self.custom_themes[theme_name] if theme_name in self.custom_themes else None
            self.theme = HeadUpDisplayTheme(theme_name, theme_dir)
            for widget in self.widget_manager.widgets:
                if disable_animation:
                    show_animations = widget.show_animations
                    widget.show_animations = False
                    widget.set_theme(self.theme)
                    widget.show_animations = show_animations
                else:
                    widget.set_theme(self.theme)
                    
            if should_reset_watch:
                self.watch_directories()
            
            self.preferences.persist_preferences({"theme_name": theme_name})

    def reload_theme(self, name=None, flags=None):
        self.theme = HeadUpDisplayTheme(self.theme.name, self.theme.theme_dir)
        for widget in self.widget_manager.widgets:
            show_animations = widget.show_animations
            widget.show_animations = False
            widget.set_theme(self.theme)
            widget.show_animations = show_animations

    def watch_directories(self):
        directories = self.theme.get_watch_directories()
        for directory in directories:
            fs.watch(directory, self.reload_theme)
            
        directories = self.preferences.get_watch_directories()
        for directory in directories:
            fs.watch(directory, self.debounce_environment_change)

        self.watching_directories = True
        
    def unwatch_directories(self):
        directories = self.theme.get_watch_directories()
        for directory in directories:
            fs.unwatch(directory, self.reload_theme)
            
        directories = self.preferences.get_watch_directories()
        for directory in directories:
            fs.unwatch(directory, self.debounce_environment_change)
            
        self.watching_directories = False

    def start_setup_id(self, id, setup_type, mouse_pos = None):
        for widget in self.widget_manager.widgets:
            if widget.enabled and ( id == "*" or widget.id == id ) and widget.setup_type != setup_type:
                widget.start_setup(setup_type, mouse_pos)
                
        self.determine_active_setup_mouse()
        
    def reload_preferences(self, _= None):
        """Reload user preferences ( in case a monitor switches or something )"""
        self.widget_manager.reload_preferences(False, self.current_talon_hud_environment)
    
    def register_poller(self, topic: str, poller: Poller, keep_alive: bool):
        self.remove_poller(topic)
        self.pollers[topic] = poller
        
        # Add a content builder to the poller
        if hasattr(self.pollers[topic], "content"):
            poller.content = HudContentBuilder(self.display_state)
        
        # Keep the poller alive even if no widgets have subscribed to its topic
        if keep_alive and not self.pollers[topic].enabled:
            self.keep_alive_pollers.append(topic)
            self.pollers[topic].enable()
        # Automatically enable the poller if it was active on restart        
        else:
            for widget in self.widget_manager.widgets:
                if topic in widget.current_topics and widget.enabled and \
                    (not hasattr(self.pollers[topic], "enabled") or not self.pollers[topic].enabled):
                    self.pollers[topic].enable()
                    break
        
    def remove_poller(self, topic: str):
        if topic in self.pollers:
            self.pollers[topic].disable()
            if hasattr(self.pollers[topic], "content"):
                self.pollers[topic].content.content = None
                self.pollers[topic].content = None
            del self.pollers[topic]
            
    def deactivate_poller(self, topic: str):
        if topic in self.pollers:
            self.pollers[topic].disable()
    
    def activate_poller(self, topic: str):
    	# Enable the poller afterwards
        if topic in self.pollers and \
            topic not in self.keep_alive_pollers and \
            (not hasattr(self.pollers[topic], "enabled") or not self.pollers[topic].enabled):
            self.pollers[topic].enable()

    def synchronize_pollers(self, disable_pollers = True, enable_pollers = True):
        attached_topics = list(self.keep_alive_pollers)
        for widget in self.widget_manager.widgets:
            if widget.current_topics and widget.enabled:
                attached_topics.extend(widget.current_topics)

        # First - Disable all pollers from making content updates to prevent race conditions with content events from occurring
        if disable_pollers:
            for topic, poller in self.pollers.items():
                if topic not in attached_topics and (hasattr(self.pollers[topic], "enabled") and self.pollers[topic].enabled):
                    self.pollers[topic].disable()

        # Then - Automatically start pollers that are connected to widgets
        if enable_pollers:
            for topic, poller in self.pollers.items():
                if topic in attached_topics and (not hasattr(self.pollers[topic], "enabled") or not self.pollers[topic].enabled):
                    self.pollers[topic].enable()                            

    # Synchronize the pollers attached to a single widget
    def synchronize_widget_poller(self, widget_id):
        current_topics = []
        for widget in self.widget_manager.widgets:
            if widget.id == widget_id:
                current_topics = widget.current_topics
                break

        for topic in current_topics:
            if topic in self.pollers and topic not in self.keep_alive_pollers:
                if widget.enabled and (not hasattr(self.pollers[topic], "enabled") or not self.pollers[topic].enabled):
                    self.pollers[topic].enable()
                elif not widget.enabled and (hasattr(self.pollers[topic], "enabled") and self.pollers[topic].enabled):
                    self.pollers[topic].disable()
                    

    # Check if the widgets are finished unloading, then disable the poller
    # This should only run when we have a state poller
    def disable_poller_check(self):
        enabled = False
        for widget in self.widget_manager.widgets:
            if not widget.cleared:
                enabled = True
                break

        if not enabled:
            for topic, poller in self.pollers.items():
                poller.disable()
            cron.cancel(self.disable_poller_job)
            self.disable_poller_job = None

    def broadcast_update(self, event: HudContentEvent):
        # Do not force a reopen of Talon HUD without explicit user permission        
        updated = False
        if not self.enabled:
            event.show = False
        
        # Restrict the content flow to only the allowed operations
        if "*" not in self.allowed_content_operations and event.operation not in self.allowed_content_operations:
            return
        
        # Claim a widget and unregister its pollers
        if event.claim > 0:
            topic = event.topic
            using_fallback = True
            widget_to_claim = None
            widgets_with_topic = []
            for widget in self.widget_manager.widgets:
                if event.topic_type in widget.topic_types and topic in widget.current_topics:
                    widgets_with_topic.append(widget)
                
                if event.topic_type in widget.topic_types and ( topic in widget.subscriptions or ("*" in widget.subscriptions and using_fallback)):
                    if topic in widget.current_topics:
                        widget_to_claim = widget
                    else:
                        widget_to_claim = widget
                        if topic in widget.subscriptions:
                            using_fallback = False

            if widget_to_claim:
                # When a new topic is published it can lay claim to a widget
                # So old pollers need to be deregistered in that case
                for widget in widgets_with_topic:
                    if widget.id != widget_to_claim.id:
                        widget.clear_topic(event.topic)
                
                updated = widget_to_claim.content_handler(event)
                self.synchronize_pollers()
        else:
            for widget in self.widget_manager.widgets:
                if event.topic_type == "variable" or (event.topic_type in widget.topic_types and \
                    (event.topic in widget.subscriptions or \
                    ("*" in widget.subscriptions and "!" + event.topic not in widget.subscriptions))):

                    current_enabled_state = widget.enabled
                    updated = widget.content_handler(event)
                    if widget.enabled != current_enabled_state:
                        if event.topic in self.pollers and event.topic not in self.keep_alive_pollers:
                            if widget.enabled:
                                self.pollers[event.topic].enable()
                            else:
                                self.pollers[event.topic].disable()
            self.synchronize_pollers()
        if updated:
            self.update_context()

    # Enable the content events to make changes to widgets and preferences
    def content_flow_enable(self):
        self.preferences.enable()
        self.allowed_content_operations = ["*"]
        
    # Restrict the content events from making non-clean up changes to widgets and preferences
    def content_flow_restrict(self):
        self.preferences.disable()
        self.allowed_content_operations = ["remove"]

    # Determine whether or not we need to have a global mouse poller
    # This poller is needed for setup modes as not all canvases block the mouse
    def determine_active_setup_mouse(self):
        has_setup_modes = False
        for widget in self.widget_manager.widgets:
            if (widget.setup_type not in ["", "mouse_drag"]):
                has_setup_modes = True
                break
    
        if has_setup_modes and not self.mouse_poller:
            self.mouse_poller = cron.interval("16ms", self.poll_mouse_pos_for_setup)
        if not has_setup_modes and self.mouse_poller:
            cron.cancel(self.mouse_poller)
            self.mouse_poller = None

    # Send mouse events to enabled widgets that have an active setup going on
    def poll_mouse_pos_for_setup(self):
        pos = ctrl.mouse_pos()
        
        if (self.prev_mouse_pos is None or numpy.linalg.norm(numpy.array(pos) - numpy.array(self.prev_mouse_pos)) > 1):
            self.prev_mouse_pos = pos
            for widget in self.widget_manager.widgets:
                if widget.enabled and widget.setup_type != "":
                    widget.setup_move(self.prev_mouse_pos)

    # Increase the page number by one on the widget if it is enabled
    def increase_widget_page(self, widget_id: str):
        for widget in self.widget_manager.widgets:
            if widget.enabled and widget.id == widget_id and isinstance(widget, LayoutWidget):
                widget.set_page_index(widget.page_index + 1)

    # Decrease the page number by one on the widget if it is enabled
    def decrease_widget_page(self, widget_id: str):
        for widget in self.widget_manager.widgets:
            if widget.enabled and widget.id == widget_id and isinstance(widget, LayoutWidget):
                widget.set_page_index(widget.page_index - 1)

    # Get the current page data
    def get_widget_pagination(self, widget_id: str) -> HudContentPage:
        page = HudContentPage(0, 0, 0)
        for widget in self.widget_manager.widgets:
            if widget.enabled and widget.id == widget_id and isinstance(widget, LayoutWidget):
                page = widget.get_content_page()
        return page

    # Move the context menu over to the given location fitting within the screen
    def move_context_menu(self, widget_id: str, pos: Point2d, buttons: list[HudButton]):
        connected_widget = None
        context_menu_widget = None
        for widget in self.widget_manager.widgets:
            if widget.enabled and widget.id == widget_id:
                connected_widget = widget
            elif widget.id == "context_menu":      
                context_menu_widget = widget
        if connected_widget and context_menu_widget:
            context_menu_widget.connect_widget(connected_widget, pos.x, pos.y, buttons)
            self.update_context()
            
    # Connect the context menu using voice
    def connect_context_menu(self, widget_id):
        connected_widget = None
        context_menu_widget = None
        for widget in self.widget_manager.widgets:
            if widget.enabled and widget.id == widget_id:
                connected_widget = widget
            elif widget.id == "context_menu":      
                context_menu_widget = widget
        
        buttons = []
        if connected_widget:
            pos_x = connected_widget.x + connected_widget.width / 2
            pos_y = connected_widget.y + connected_widget.height
            buttons = connected_widget.buttons
        
            if context_menu_widget:
                context_menu_widget.connect_widget(connected_widget, pos_x, pos_y, buttons)
                self.update_context()
    
    # Hide the context menu
    # Generally you want to do this when you click outside of the menu itself
    def hide_context_menu(self, _ = None):
        context_menu_widget = None    
        for widget in self.widget_manager.widgets:
            if widget.id == "context_menu" and widget.enabled:      
                context_menu_widget = widget
                break
        
        if context_menu_widget:
            context_menu_widget.disconnect_widget()
            self.update_context()
    
    # Active a given choice for a given widget
    def activate_choice(self, choice_string):
        widget_id, choice_index = choice_string.split("|")
        for widget in self.widget_manager.widgets:
            if widget.id == widget_id:
                if isinstance(widget, HeadUpChoicePanel):
                    widget.select_choice(int(choice_index))
                else:
                    widget.click_button(int(choice_index))
        self.update_context()
                    
    def activate_enabled_voice_command(self, voice_command):
        if voice_command in self.enabled_voice_commands:
            self.enabled_voice_commands[voice_command]()

    # Updates the context based on the current HUD state
    # This needs to be done on user actions - Automatic flows need higher scrutiny
    def update_context(self):        
        widget_names = {}
        choices = {}
        quick_choices = {}
        numerical_choices = {}
        themes = {}
        enabled_voice_commands = {}
        
        themes_directory = os.path.dirname(os.path.abspath(__file__)) + "/themes"
        themes_list = os.listdir(themes_directory)
        for theme in themes_list:
            if theme != "_base_theme":
                themes[string_to_speakable_string(theme)] = theme
        for custom_theme_name in self.custom_themes:
            themes[string_to_speakable_string(custom_theme_name)] = custom_theme_name
        
        for widget in self.widget_manager.widgets:
            current_widget_names = [string_to_speakable_string(widget.id)]        
            if isinstance(widget, HeadUpTextPanel):
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

            # Add extra voice commands ( for instance, ones alluded to in text )
            if widget.enabled and isinstance(widget, HeadUpTextPanel) and widget.panel_content.voice_commands:
                for index, voice_command in enumerate(widget.panel_content.voice_commands):
                    enabled_voice_command = string_to_speakable_string(voice_command.command)
                    if enabled_voice_command:
                        enabled_voice_commands[enabled_voice_command] = voice_command.callback
             
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
        
        # Make sure the list is never empty to prevent #495
        if len(choices) == 0:
            choices["head up choice empty command"] = "|"
        
        ctx.lists["user.talon_hud_numerical_choices"] = numerical_choices
        ctx.lists["user.talon_hud_widget_names"] = widget_names
        ctx.lists["user.talon_hud_choices"] = choices
        ctx.lists["user.talon_hud_quick_choices"] = quick_choices
        ctx.lists["user.talon_hud_themes"] = themes
        
        self.enabled_voice_commands = enabled_voice_commands
        ctx.lists["user.talon_hud_widget_enabled_voice_commands"] = enabled_voice_commands.keys()

    def hud_environment_change(self, hud_environment: str):
        if self.current_talon_hud_environment != hud_environment:
            # Temporarily disable preference persisting during the transition between environments
            # As content updates during the transition can override previous files
            self.content_flow_restrict()
            self.current_talon_hud_environment = hud_environment
            
            # Add a debouncer for the environment change to reduce flickering on transitioning
            cron.cancel(self.update_environment_debouncer)
            self.update_environment_debouncer = cron.after("200ms", self.debounce_environment_change)

    def debounce_environment_change(self, _=None, __=None):
        reload_theme = self.widget_manager.reload_preferences(True, self.current_talon_hud_environment)
        # Switch the theme and make sure there is no lengthy animation between modes 
        # as they can happen quite frequently
        self.switch_theme(reload_theme, True)

        # Re-enable the content flow including persistence after transitions have been made
        self.synchronize_pollers(disable_pollers=True, enable_pollers=False)
        self.content_flow_enable()
        self.synchronize_pollers(disable_pollers=False, enable_pollers=True)        

preferences = HeadUpDisplayUserPreferences("", CURRENT_TALON_HUD_VERSION) 
hud = HeadUpDisplay(hud_content, preferences)

def hud_start():
    global hud    
    hud.start()

app.register("ready", hud_start)

@mod.action_class
class Actions:
                
    def hud_enable():
        """Enables the HUD"""
        global hud
        hud.enable(True)

    def hud_disable():
        """Disables the HUD"""
        global hud
        hud.disable(True)

    def hud_persist_preferences():
        """Saves the HUDs preferences"""
        global hud
        hud.debounce_widget_preferences()

    def hud_enable_id(id: str):
        """Enables a specific HUD element"""
        global hud        
        hud.enable_id(id)
        
    def hud_set_widget_preference(id: str, property: str, value: Any):
        """Set a specific widget preference"""
        global hud        
        hud.set_widget_preference(id, property, value, True)        
        
    def hud_widget_subscribe_topic(id: str, topic: str):
        """Subscribe to a specific type of content on a widget"""
        global hud
        hud.subscribe_content_id(id, topic)
        
    def hud_widget_unsubscribe_topic(id: str, topic: str):
        """Unsubscribe from a specific type of content on a widget"""
        global hud
        hud.unsubscribe_content_id(id, topic)
        
    def hud_disable_id(id: str):
        """Disables a specific HUD element"""
        global hud
        hud.disable_id(id)
        
    def hud_switch_theme(theme_name: str):
        """Switches the UI theme"""
        global hud
        hud.switch_theme(theme_name)
        
    def hud_set_setup_mode(id: str, setup_mode: str):
        """Starts a setup mode which can change position"""
        global hud
        hud.start_setup_id(id, setup_mode)

    def hud_set_setup_mode_multi(ids: list[str], setup_mode: str):
        """Starts a setup mode which can change position for multiple widgets at the same time"""
        global hud
        
        # In case we are dealing with drag, we can allow multiple widgets to be dragged at the same time
        mouse_pos = None
        if (len(ids) > 1 and setup_mode == "position"):
            mouse_pos = ctrl.mouse_pos()
        
        for id in ids:
            hud.start_setup_id(id, setup_mode, mouse_pos)
                
    def hud_show_context_menu(widget_id: str, pos_x: int, pos_y: int, buttons: list[HudButton]):
        """Show the context menu for a specific widget id"""
        hud.move_context_menu(widget_id, Point2d(pos_x, pos_y), buttons)
        
    def hud_hide_context_menu():
        """Show the context menu for a specific widget id"""
        hud.hide_context_menu()
        
    def hud_increase_widget_page(widget_id: str):
        """Increase the content page of the widget if it has pages available"""
        global hud
        hud.increase_widget_page(widget_id)

    def hud_decrease_widget_page(widget_id: str):
        """Decrease the content page of the widget if it has pages available"""
        global hud
        hud.decrease_widget_page(widget_id)
        
    def hud_get_widget_pagination(widget_id: str) -> HudContentPage:
        """Get the pagination information of the widget"""
        global hud
        return hud.get_widget_pagination(widget_id)
        
    def hud_widget_options(widget_id: str):
        """Connect the widget to the context menu to show the options"""
        global hud
        hud.connect_context_menu(widget_id)
        
    def hud_activate_choice(choice_string: str):
        """Activate a choice available on the screen"""    
        global hud
        hud.activate_choice(choice_string)
        
    def hud_activate_enabled_voice_command(enabled_voice_command: str):
        """Activate a defined voice command attached to an enabled widget"""
        global hud
        hud.activate_enabled_voice_command(enabled_voice_command)
        
    def hud_activate_choices(choice_string_list: list[str]):
        """Activate multiple choices available on the screen"""    
        global hud
        for choice_string in choice_string_list:
            hud.activate_choice(choice_string)
        
    def hud_add_poller(topic: str, poller: Poller, keep_alive: bool = False):
        """Add a content poller / listener to the HUD"""    
        global hud
        hud.register_poller(topic, poller, keep_alive)
        
    def hud_remove_poller(topic: str):
        """Remove a content poller / listener to the HUD"""    
        global hud
        hud.remove_poller(topic)
        
    def hud_activate_poller(topic: str):
        """Enables a poller and claims a widget"""
        global hud
        hud.activate_poller(topic)
        
    def hud_deactivate_poller(topic: str):
        """Disables a poller"""    
        global hud
        hud.deactivate_poller(topic)
        
    def hud_get_theme() -> HeadUpDisplayTheme:
        """Get the current theme object from the HUD"""
        global hud
        return hud.theme
        
    def hud_register_theme(theme_name: str, theme_dir: str):
        """Add a theme directory from outside of the HUD to the possible themes"""
        global hud
        hud.add_theme(theme_name, theme_dir)
        
    def hud_watch_directories():
        """Watch the theme and preferences directories for changes - This gives a performance penalty and should only be used during development"""
        global hud
        hud.watch_directories()
        
    def hud_unwatch_directories():
        """Stop watching for changes in the theme directories"""
        global hud
        hud.unwatch_directories()