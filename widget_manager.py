import os
from talon import ui
from user.talon_hud.preferences import HeadUpDisplayUserPreferences
from user.talon_hud.base_widget import BaseWidget
from user.talon_hud.widgets.statusbar import HeadUpStatusBar
from user.talon_hud.widgets.eventlog import HeadUpEventLog
from user.talon_hud.widgets.abilitybar import HeadUpAbilityBar
from user.talon_hud.widgets.textpanel import HeadUpTextPanel
from user.talon_hud.widgets.choicepanel import HeadUpChoicePanel
from user.talon_hud.widgets.documentationpanel import HeadUpDocumentationPanel
from user.talon_hud.widgets.walkthroughpanel import HeadUpWalkThroughPanel
from user.talon_hud.widgets.contextmenu import HeadUpContextMenu
from user.talon_hud.theme import HeadUpDisplayTheme

semantic_directory = os.path.dirname(os.path.abspath(__file__))
user_preferences_file_dir =  semantic_directory + "/preferences/"
old_user_preferences_file_location = user_preferences_file_dir + "preferences.csv"
user_preferences_file_location = user_preferences_file_dir + "widget_settings.csv"

class HeadUpWidgetManager:
    """Manages widgets and their positioning in relation to the available screens"""
    default_screen_rect: ui.Rect
    
    # TODO Maybe scale content based on real world screen dimensions for clarity?
    default_screen_mm_size: list
    
    previous_screen_rects: list[ui.Rect]
    theme: HeadUpDisplayTheme
    preferences: HeadUpDisplayUserPreferences
    widgets: list[BaseWidget]
    
    def __init__(self, preferences: HeadUpDisplayUserPreferences, theme: HeadUpDisplayTheme):
        self.default_screen_rect = ui.Rect(0, 0, 1920, 1080)
        self.default_screen_mm_size = [527.0, 296.0]
        
        self.previous_screen_rects = []
        self.preferences = preferences
        self.theme = theme
        self.initial_load_preferences()
        self.load_widgets()
        
        # Reload the preferences according to the monitor sizes if the given file does not exist
        if not os.path.exists(self.preferences.get_screen_preferences_filepath(ui.screens())):
            self.reload_preferences(True)
    
    def load_widgets(self):
        """Load the user defined widgets"""
        
        # TODO - Make the widgets properly user-definable
        # By making them addable and removable
        # With subscribed content, topics etc for specific widgets
        # For now, we will just use the default widgets taken from the display widgets array
        self.widgets = self.get_default_widgets()
        
        self.previous_screen_rects = []
        for screen in ui.screens():
            self.previous_screen_rects.append(ui.Rect(screen.x, screen.y, screen.width, screen.height))
    
    def initial_load_preferences(self):
        user_preferences_screen_file_path = self.preferences.get_screen_preferences_filepath(ui.screens())
        
        # Migration from old preferences file to new split files
        if not os.path.exists(user_preferences_file_location) and os.path.exists(old_user_preferences_file_location):
            fh = open(old_user_preferences_file_location, 'r')
            lines = fh.readlines()
            fh.close()
            
            monitor_lines = list(filter(lambda line: [line for ext in self.preferences.monitor_related_pref_endings if(ext in line)], lines))
            screen_file_path = user_preferences_screen_file_path
            fh = open(screen_file_path, 'w')
            fh.write("".join(monitor_lines))
            fh.close()
            
            setting_lines = list(filter(lambda line: line not in monitor_lines, lines))            
            fh = open(user_preferences_file_location, 'w')
            fh.write("".join(setting_lines))
            fh.close()            
            
            # Remove the old preferences file
            os.remove(old_user_preferences_file_location)
        
        if not os.path.exists(user_preferences_file_location):
            self.preferences.persist_preferences(self.preferences.default_prefs, True)
                
        self.preferences.load_preferences(user_preferences_screen_file_path)
    
    def reload_preferences(self, force_reload=False):
        
        # Check if the screen dimensions have changed
        current_screen_rects = []
        dimensions_changed = force_reload
        if dimensions_changed == False:
            for index, screen in enumerate(ui.screens()):
                current_screen_rects.append(ui.Rect(screen.x, screen.y, screen.width, screen.height))
                if index < len(self.previous_screen_rects) and dimensions_changed == False:
                    previous_screen_rect = self.previous_screen_rects[index]
                    dimensions_changed = previous_screen_rect.x != screen.x or \
                        previous_screen_rect.y != screen.y or \
                        previous_screen_rect.width != screen.width or \
                        previous_screen_rect.height != screen.height
            dimensions_changed = dimensions_changed or len(current_screen_rects) != len(self.previous_screen_rects)
        
        if dimensions_changed:
            screen_preferences_file = self.preferences.get_screen_preferences_filepath(current_screen_rects)
            if not os.path.exists(screen_preferences_file):
                # TODO DETERMINE DIFFERENCE BETWEEN FORMER SCREENS AND CURRENT SCREENS FOR WIDGETS
                # TO MAKE SURE THE SETTINGS ARE SET WELL
                self.preferences.persist_preferences(self.preferences.default_prefs, True)
            else:
                self.preferences.load_preferences()
        
        # Apply the new preferences to the widgets directly
        for widget in self.widgets:
            # First cancel any set up to make sure there won't be some weird collision going on with persistence
            if widget.setup_type != "":
                widget.start_setup("cancel")
            widget.load(self.preferences.prefs, False)
            widget.start_setup("reload")
            
        # Set the screen info to be used for comparison in case the screen changes later
        self.previous_screen_rects = current_screen_rects
    
    def get_default_widgets(self):
        """Load widgets to give an optional default user experience that allows all the options"""
        
        self.previous_screen_rects = [
            ui.Rect(
                self.default_screen_rect.x, 
                self.default_screen_rect.y, 
                self.default_screen_rect.width, 
                self.default_screen_rect.height)
            ]
        
        return [
            self.load_widget("status_bar", "status_bar"),
            self.load_widget("event_log", "event_log"),
            self.load_widget("Text panel", "text_panel", {'topics': ['*']}),
            # Extra text boxes can be defined to be assigned to different topics
            # self.load_widget("Text box two", "text_panel", {'topics': ['your_topic_here'], 'current_topic': 'your_topic_here'}),

            self.load_widget("Documentation", "documentation_panel", {'topics': ['documentation']}),
            self.load_widget("Choices", "choice_panel", {'topics': ['choice'], 'current_topic': 'choice'}),
            self.load_widget("ability_bar", "ability_bar"),
            self.load_widget("walk_through", "walk_through_panel", {'topics': ['walk_through']}),
            
            # Special widgets that have varying positions            
            self.load_widget("context_menu", "context_menu")
        ]
        
    def load_widget(self, id: str, type: str, subscriptions = None) -> BaseWidget:
        """Load a specific widget type with the id"""
        if type == "status_bar":
            return self.load_status_bar(id, self.preferences.prefs)
        elif type == "ability_bar":
            return self.load_ability_bar(id, self.preferences.prefs)
        elif type == "event_log":
            return self.load_event_log(id, self.preferences.prefs)
        elif type == "context_menu":
            return self.load_context_menu(id, self.preferences.prefs)
        
        # All widgets with specific subscriptions tied to them        
        elif type == "text_panel":
            return self.load_text_panel(id, self.preferences.prefs, subscriptions)
        elif type == "documentation_panel":
            return self.load_documentation_panel(id, self.preferences.prefs, subscriptions)
        elif type == "choice_panel":
            return self.load_choice_panel(id, self.preferences.prefs, subscriptions)
        elif type == "walk_through_panel":
            return self.load_walk_through_panel(id, self.preferences.prefs, subscriptions)
            
    def load_status_bar(self, id, preferences=None):
        """Load a status bar widget with the given preferences"""
        return HeadUpStatusBar(id, preferences, self.theme)

    def load_event_log(self, id, preferences=None):
        """Load an event log widget with the given preferences"""
        return HeadUpEventLog(id, preferences, self.theme)

    def load_ability_bar(self, id, preferences=None):
        """Load an ability bar widget with the given preferences"""
        return HeadUpAbilityBar(id, preferences, self.theme)
        
    def load_context_menu(self, id, preferences=None):
        """Load a context menu widget with the given preferences"""
        return HeadUpContextMenu(id, preferences, self.theme)

    def load_text_panel(self, id, preferences=None, subscriptions=None):
        """Load a text panel widget with the given preferences"""
        return HeadUpTextPanel(id, preferences, self.theme, subscriptions)
        
    def load_documentation_panel(self, id, preferences=None, subscriptions=None):
        """Load a documentation panel widget with the given preferences"""
        return HeadUpDocumentationPanel(id, preferences, self.theme, subscriptions)
        
    def load_choice_panel(self, id, preferences=None, subscriptions=None):
        """Load a choice panel widget with the given preferences"""
        return HeadUpChoicePanel(id, preferences, self.theme, subscriptions)
        
    def load_walk_through_panel(self, id, preferences=None, subscriptions=None):
        """Load a choice panel widget with the given preferences"""
        return HeadUpWalkThroughPanel(id, preferences, self.theme, subscriptions)
    