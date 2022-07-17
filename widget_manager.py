import os
import numpy
import copy
from typing import Dict
from talon import ui, settings
from .preferences import HeadUpDisplayUserPreferences
from .base_widget import BaseWidget
from .widgets.statusbar import HeadUpStatusBar
from .widgets.eventlog import HeadUpEventLog
from .widgets.abilitybar import HeadUpAbilityBar
from .widgets.textpanel import HeadUpTextPanel
from .widgets.choicepanel import HeadUpChoicePanel
from .widgets.documentationpanel import HeadUpDocumentationPanel
from .widgets.walkthroughpanel import HeadUpWalkthroughPanel
from .widgets.contextmenu import HeadUpContextMenu
from .widgets.cursortracker import HeadUpCursorTracker
from .widgets.screenoverlay import HeadUpScreenOverlay
from .theme import HeadUpDisplayTheme
from .event_dispatch import HeadUpEventDispatch
from .configuration import hud_get_configuration
from .focus_manager import HeadUpFocusManager
from .html_generator import HeadUpHtmlGenerator

user_preferences_file_dir = hud_get_configuration("user_preferences_folder")
user_preferences_file_location = os.path.join(user_preferences_file_dir, "widget_settings.csv")

class HeadUpWidgetManager:
    """Manages widgets and their positioning in relation to the available screens"""
    default_screen_rect: ui.Rect
    
    # TODO Maybe scale content based on real world screen dimensions for clarity?
    default_screen_mm_size: list
    
    previous_screen_rects: list[ui.Rect]
    previous_talon_hud_environment = ""
    theme: HeadUpDisplayTheme
    event_dispatch: HeadUpEventDispatch
    preferences: HeadUpDisplayUserPreferences
    widgets: list[BaseWidget]
    focus_manager: HeadUpFocusManager
    
    def __init__(self, preferences: HeadUpDisplayUserPreferences, theme: HeadUpDisplayTheme, event_dispatch: HeadUpEventDispatch):
        self.default_screen_rect = ui.Rect(0, 0, 1920, 1080)
        self.default_screen_mm_size = [527.0, 296.0]
        
        self.focus_manager = HeadUpFocusManager(self, event_dispatch)
        self.html_generator = HeadUpHtmlGenerator(theme, self.focus_manager)
        self.previous_talon_hud_environment = ""
        self.previous_screen_rects = []
        self.preferences = preferences
        self.theme = theme
        self.event_dispatch = event_dispatch
        self.initial_load_preferences()
        self.load_widgets()
        
        # Reload the preferences according to the monitor sizes if the given file does not exist
        if not os.path.exists(self.preferences.get_screen_preferences_filepath(ui.screens())):
            self.previous_screen_rects = [
                ui.Rect(
                    self.default_screen_rect.x, 
                    self.default_screen_rect.y, 
                    self.default_screen_rect.width, 
                    self.default_screen_rect.height)
                ]
            self.reload_preferences(True, self.previous_talon_hud_environment)
    
    def load_widgets(self):
        """Load the user defined widgets"""
        
        # TODO - Make the widgets properly user-definable
        # By making them addable and removable
        # With subscribed content, topics etc for specific widgets
        # For now, we will just use the default widgets taken from the display widgets array
        self.widgets = self.get_default_widgets()
        self.focus_manager.init_widgets()
        
        self.previous_screen_rects = []
        for screen in ui.screens():
            self.previous_screen_rects.append(ui.Rect(screen.x, screen.y, screen.width, screen.height))
    
    def destroy(self):
        self.widgets = []
        self.focus_manager.destroy()
        self.focus_manager = None
    
    def is_focused(self):
        return self.focus_manager and self.focus_manager.focused
        
    def focus(self, widget_id: str = None, node_id: int = -1):
        if self.focus_manager:
            self.focus_manager.focus_path(None)

    def blur(self):
        if self.focus_manager:
            self.focus_manager.blur()
    
    def initial_load_preferences(self):
        user_preferences_screen_file_path = self.preferences.get_screen_preferences_filepath(ui.screens())
        if not os.path.exists(user_preferences_file_location):
            self.preferences.persist_preferences(self.preferences.default_prefs, True)
        self.preferences.load_preferences(user_preferences_screen_file_path)
    
    def reload_preferences(self, force_reload=False, current_hud_environment="") -> str:        
        # Check if the screen dimensions have changed
        current_screen_rects = []
        dimensions_changed = force_reload
        for index, screen in enumerate(ui.screens()):
            current_screen_rects.append(ui.Rect(screen.x, screen.y, screen.width, screen.height))
            if index < len(self.previous_screen_rects) and dimensions_changed == False:
                previous_screen_rect = self.previous_screen_rects[index]
                if previous_screen_rect.x != screen.x or \
                    previous_screen_rect.y != screen.y or \
                    previous_screen_rect.width != screen.width or \
                    previous_screen_rect.height != screen.height:
                    dimensions_changed = True
        dimensions_changed = dimensions_changed or len(current_screen_rects) != len(self.previous_screen_rects)

        # Reload the main preferences in case the Talon HUD mode changed
        new_theme = self.preferences.prefs["theme_name"]
        environment_changed = current_hud_environment != self.previous_talon_hud_environment
        if environment_changed:
            self.preferences.set_hud_environment(current_hud_environment)
            
            # Prevent two reloads after another if the monitor has also changed
            if not dimensions_changed:
                self.preferences.load_preferences(self.preferences.get_main_preferences_filename())
            self.previous_talon_hud_environment = current_hud_environment
        
        if dimensions_changed:
            screen_preferences_file = self.preferences.get_screen_preferences_filepath(current_screen_rects)
            
            # If the dimensions have changed, but no preferences file is available,
            # Determine the positioning of the widgets dynamically compared to the last screen settings
            if not os.path.exists(screen_preferences_file):
                self.preferences.load_preferences( screen_preferences_file )
                
                new_preferences = {}
                for key in self.preferences.default_prefs.keys():
                    new_preferences[key] = self.preferences.default_prefs[key]
                
                for widget in self.widgets:
                    widget_prefs = self.get_widget_preference(widget, current_screen_rects)
                    for key in widget_prefs.keys():
                        new_preferences[key] = widget_prefs[key]
                
                self.preferences.persist_preferences( new_preferences )
            else:
                self.preferences.load_preferences( screen_preferences_file )
                
        if environment_changed:
            new_theme = self.preferences.prefs["theme_name"]            

        # Apply the new preferences to the widgets directly
        for widget in self.widgets:
            # First cancel any set up to make sure there won"t be some weird collision going on with persistence
            if widget.setup_type != "":
                widget.start_setup("cancel")
            widget.load(self.preferences.prefs, False, environment_changed)
            if widget.enabled:
                widget.start_setup("reload")

        # Set the screen info to be used for comparison in case the screen changes later
        self.previous_screen_rects = current_screen_rects
        return new_theme
    
    def get_widget_preference(self, widget, current_screens) -> Dict:
        widget_screen = None
        for screen in self.previous_screen_rects:
            if widget.x >= screen.x and widget.x <= screen.x + screen.width \
                and widget.y >= screen.y and widget.y <= screen.y + screen.height:
                widget_screen = screen
                break
        
        widget_preferences = widget.preferences
        
        if widget_screen:
            anchor_point = self.determine_widget_anchor_point(widget, widget_screen)
            
            # Reposition Y coordinates based on difference between previous and current screen
            widget_top = numpy.array([0, widget.y])
            widget_limit_top = numpy.array([0, widget.limit_y])
            if anchor_point[0] == "top":
                screen_top = numpy.array([0, widget_screen.y])
                
                widget_preferences.y = numpy.linalg.norm(screen_top - widget_top)
                widget_preferences.limit_y = numpy.linalg.norm(screen_top - widget_limit_top)
            elif anchor_point[0] == "center":
                widget_center = numpy.array([0, widget.y + widget.height / 2])
                widget_limit_center = numpy.array([0, widget.limit_y + widget.limit_height / 2])                
                screen_center = numpy.array([0, widget_screen.y + widget_screen.height / 2])
                
                direction = 1 if screen_center[1] < widget_center[1] else -1
                limit_direction = 1 if screen_center[0] < widget_limit_center[0] else -1
                widget_preferences.y = ( current_screens[0].y + current_screens[0].height / 2 ) + \
                    numpy.linalg.norm(screen_center - widget_center) * direction - \
                    widget.height / 2
                widget_preferences.limit_y = ( current_screens[0].y + current_screens[0].height / 2 ) + \
                    numpy.linalg.norm(screen_center - widget_limit_center) * limit_direction - \
                    widget.limit_height / 2
            else:
                screen_bottom = numpy.array([0, widget_screen.y + widget_screen.height])
                
                widget_preferences.y = ( current_screens[0].y + current_screens[0].height ) - \
                    numpy.linalg.norm(screen_bottom - widget_top)
                widget_preferences.limit_y = ( current_screens[0].y + current_screens[0].height ) - \
                    numpy.linalg.norm(screen_bottom - widget_limit_top)
                        
            # Reposition X coordinates based on difference between previous and current screen
            widget_left = numpy.array([widget.x, 0])
            widget_limit_left = numpy.array([widget.limit_x, 0])
            if anchor_point[1] == "left":
                screen_left = numpy.array([widget_screen.x, 0])
                
                widget_preferences.x = current_screens[0].x + numpy.linalg.norm(screen_left - widget_left)
                widget_preferences.limit_x = current_screens[0].x + numpy.linalg.norm(screen_left - widget_limit_left)
            elif anchor_point[1] == "center":
                screen_center = numpy.array([widget_screen.x + widget_screen.width / 2,0])
                
                widget_center = numpy.array([widget.x + widget.width / 2, 0])
                widget_limit_center = numpy.array([widget.limit_x + widget.limit_width / 2, 0])
                
                direction = 1 if screen_center[0] < widget_center[0] else -1
                limit_direction = 1 if screen_center[0] < widget_limit_center[0] else -1                
                widget_preferences.x = ( current_screens[0].x + current_screens[0].width / 2 ) + \
                    numpy.linalg.norm(screen_center - widget_center) * direction - \
                    widget.width / 2
                widget_preferences.limit_x = ( current_screens[0].x + current_screens[0].width / 2 ) + \
                    numpy.linalg.norm(screen_center - widget_limit_center) * limit_direction - \
                    widget.limit_width / 2
            else:
                screen_right = numpy.array([widget_screen.x + widget_screen.width,0])
                
                widget_preferences.x = ( current_screens[0].x + current_screens[0].width ) - \
                    numpy.linalg.norm(screen_right - widget_left)
                widget_preferences.limit_x = ( current_screens[0].x + current_screens[0].width ) - \
                    numpy.linalg.norm(screen_right - widget_limit_left)
                    
            widget_preferences.y = int(widget_preferences.y)
            widget_preferences.limit_y = int(widget_preferences.limit_y)
            widget_preferences.x = int(widget_preferences.x)
            widget_preferences.limit_x = int(widget_preferences.limit_x)

        return widget_preferences.export(widget.id)
    
    def determine_widget_anchor_point(self, widget, widget_screen):
        # Determine anchor position for repositioning widget on the screen
        
        anchor_point = ["top", "left"]
        width_threshold = widget_screen.width / 2
        height_threshold = widget_screen.height / 2
        
        widget_top_left = numpy.array([widget.limit_x, widget.limit_y])
        widget_center = numpy.array([widget.limit_x + widget.limit_width / 2, 
            widget.limit_y + widget.limit_height / 2])
        widget_right = numpy.array([widget.limit_x + widget.limit_width, 
            widget.limit_y])
        widget_bottom = numpy.array([widget.limit_x, widget.limit_y + widget.limit_height])
            
        screen_top = numpy.array([widget_screen.x, widget_screen.y])
        screen_vertical_center = numpy.array([widget_screen.x, widget_screen.y + widget_screen.height / 2])
        screen_bottom = numpy.array([widget_screen.x, widget_screen.y + widget_screen.height])
        screen_left = screen_top
        screen_horizontal_center = numpy.array([widget_screen.x + widget_screen.width / 2, widget_screen.y])
        screen_right = numpy.array([widget_screen.x + widget_screen.width, widget_screen.y])
        
        distance_left = numpy.linalg.norm(widget_top_left - screen_left)
        distance_horizontal_center = numpy.linalg.norm(widget_center - screen_horizontal_center)
        distance_right = numpy.linalg.norm(widget_right - screen_right)            
        distance_top = numpy.linalg.norm(widget_top_left - screen_top)
        distance_vertical_center = numpy.linalg.norm(widget_center - screen_vertical_center)
        distance_bottom = numpy.linalg.norm(widget_bottom - screen_bottom)
        
        if distance_vertical_center < distance_bottom and distance_vertical_center < distance_top:
            anchor_point[0] = "center"
        elif distance_bottom < distance_top and distance_bottom < distance_vertical_center:
            anchor_point[0] = "bottom"
        
        if distance_horizontal_center < distance_right and distance_horizontal_center < distance_left:
            anchor_point[1] = "center"
        elif distance_right < distance_left and distance_right < distance_horizontal_center:
            anchor_point[1] = "right"
        
        return anchor_point            
    
    def get_default_widgets(self):
        """Load widgets to give an optional default user experience that allows all the options"""
        default_status_topics = ["mode_toggle", "mode_option", "microphone_toggle_option", "language_option", "programming_option", "focus_toggle_option"]
        
        return [
            self.load_widget("status_bar", "status_bar", ["*"], default_status_topics ),
            self.load_widget("event_log", "event_log", ["command", "error", "warning", "event", "success", "narrate"]),
            self.load_widget("Text panel", "text_panel", ["*"]),
            # Extra text boxes can be defined to be assigned to different topics
            # self.load_widget("Text box two", "text_panel", ["scope"], ["scope"]),

            self.load_widget("Documentation", "documentation_panel", ["documentation"]),
            self.load_widget("Choices", "choice_panel", ["choice"]),
            self.load_widget("ability_bar", "ability_bar", ["*"]),
            self.load_widget("walkthrough", "walkthrough_panel", ["*"]),
            
            # Special widgets that have varying positions            
            self.load_widget("context_menu", "context_menu", ["*"]),
            self.load_widget("cursor_tracker", "cursor_tracker", ["*"]),
            self.load_widget("screen_overlay", "screen_overlay", ["*"]),
        ]
        
    def load_widget(self, id: str, type: str, subscriptions = None, current_topics = None) -> BaseWidget:
        """Load a specific widget type with the id"""
        if type == "status_bar":
            return self.load_status_bar(id, self.preferences.prefs, subscriptions, current_topics)
        elif type == "ability_bar":
            return self.load_ability_bar(id, self.preferences.prefs, subscriptions, current_topics)
        elif type == "event_log":
            return self.load_event_log(id, self.preferences.prefs, subscriptions, current_topics)
        elif type == "context_menu":
            return self.load_context_menu(id, self.preferences.prefs, subscriptions, current_topics)
        elif type == "cursor_tracker":
            return self.load_cursor_tracker(id, self.preferences.prefs, subscriptions, current_topics)
        elif type == "screen_overlay":
            return self.load_screen_overlay(id, self.preferences.prefs, subscriptions, current_topics)
        elif type == "text_panel":
            return self.load_text_panel(id, self.preferences.prefs, subscriptions, current_topics)
        elif type == "documentation_panel":
            return self.load_documentation_panel(id, self.preferences.prefs, subscriptions, current_topics)
        elif type == "choice_panel":
            return self.load_choice_panel(id, self.preferences.prefs, subscriptions, current_topics)
        elif type == "walkthrough_panel":
            return self.load_walkthrough_panel(id, self.preferences.prefs, subscriptions, current_topics)
            
    def load_status_bar(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load a status bar widget with the given preferences"""
        return HeadUpStatusBar(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)

    def load_event_log(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load an event log widget with the given preferences"""
        return HeadUpEventLog(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)

    def load_ability_bar(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load an ability bar widget with the given preferences"""
        return HeadUpAbilityBar(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)
        
    def load_context_menu(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load a context menu widget with the given preferences"""
        return HeadUpContextMenu(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)
        
    def load_cursor_tracker(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load a cursor tracker widget with the given preferences"""
        return HeadUpCursorTracker(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)
        
    def load_screen_overlay(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load a screen overlay widget with the given preferences"""
        return HeadUpScreenOverlay(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)

    def load_text_panel(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load a text panel widget with the given preferences"""
        return HeadUpTextPanel(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)
        
    def load_documentation_panel(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load a documentation panel widget with the given preferences"""
        return HeadUpDocumentationPanel(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)
        
    def load_choice_panel(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load a choice panel widget with the given preferences"""
        return HeadUpChoicePanel(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)
        
    def load_walkthrough_panel(self, id, preferences=None, subscriptions = None, current_topics = None):
        """Load a choice panel widget with the given preferences"""
        return HeadUpWalkthroughPanel(id, preferences, self.theme, self.event_dispatch, subscriptions, current_topics)
