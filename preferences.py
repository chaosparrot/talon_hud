# If you want a different preferences folder - Comment the lines marked #default and uncomment the lines marked with # custom
import os
from talon import ui
import copy
from .configuration import hud_get_configuration

user_preferences_file_dir = hud_get_configuration("user_preferences_folder")
widget_settings_file_ending = "widget_settings.csv"
user_preferences_file_location = os.path.join(user_preferences_file_dir, widget_settings_file_ending)

# Loads and persists all the data based on the users preferences
# To keep the display state consistent across sessions
class HeadUpDisplayUserPreferences:
    
    persisting_enabled = False
    
    monitor_file_path = None
    default_prefs = {
        "version": "0.6",
        "show_animations": True,
        "enabled": False,
        "auto_focus": True,        
        "theme_name": "light",
        "audio_enabled": False,
        "audio_volume": "75",
    }
    
    # Keep the base preferences available as well
    # To make sure we can keep HUD environments as specific as possible
    base_prefs = {}
    prefs = {}
    content_prefs = {}

    monitor_related_pref_endings = ("_x", "_y", "_width", "_height",
        "_limit_x", "_limit_y", "_limit_width", "_limit_height",
        "_font_size", "_alignment", "_expand_direction")
    
    boolean_keys = ["enabled", "show_animations", "audio_enabled", "auto_focus"]
    hud_environment = ""
    
    def __init__(self, hud_environment = "", hud_version = 5):
        self.hud_environment = hud_environment
        self.load_preferences(self.get_screen_preferences_filepath(ui.screens()))
        self.hud_version = hud_version
    
    def set_hud_environment(self, hud_environment):
        self.hud_environment = hud_environment
        
    def enable(self):
        self.persisting_enabled = True
        
    def disable(self):
        self.persisting_enabled = False
        
    def get_watch_directories(self):
        screens = ui.screens()
        watch_list = [self.get_main_preferences_filename(), self.get_screen_preferences_filepath(screens)]
        if self.hud_environment:
            temp_environment = self.hud_environment
            self.hud_environment = ""
            watch_list.extend([self.get_main_preferences_filename(), self.get_screen_preferences_filepath(screens)])
            self.hud_environment = temp_environment
    
        return watch_list
    
    # Get the preferences filename for the current monitor dimensions
    def get_screen_preferences_filepath(self, screens):
        hud_environment = self.hud_environment
        talon_hud_environment = "" if hud_environment == None or hud_environment == "" else hud_environment + "_"    
        preferences_title = talon_hud_environment + "monitor"
        for screen in screens:
            preferences_postfix = []
            preferences_postfix.append(str(int(screen.x)))
            preferences_postfix.append(str(int(screen.y)))
            preferences_postfix.append(str(int(screen.width)))
            preferences_postfix.append(str(int(screen.height)))
            preferences_title += "(" + "_".join(preferences_postfix) + ")"
        preferences_title += ".csv"
        return os.path.join(user_preferences_file_dir, preferences_title)
    
    def load_default_preferences(self):
        preferences = {}
        for key, value in self.default_prefs.items():
            preferences[key] = value
        
        if self.hud_environment != "":
            lines = []
            real_hud_environment = self.hud_environment
            self.hud_environment = ""
            monitor_file_path = self.get_screen_preferences_filepath(ui.screens())
            
            file_path = self.get_main_preferences_filename()
            if os.path.exists(file_path):
               fh = open(file_path, "r")
               lines.extend(fh.readlines())
               fh.close()
                                  
            if monitor_file_path is not None:
               if os.path.exists(monitor_file_path):
                   fh = open(monitor_file_path, "r")
                   lines.extend(fh.readlines())
                   fh.close()

            preferences = {}
            for key, value in self.default_prefs.items():
                preferences[key] = value

            # Clear context_menu and walk_through stuff so the new sizes can be applied
            migrate_v05 = False

            # Override defaults with file values
            for index,line in enumerate(lines):
                split_line = line.strip("\n").split(",", 1)
                key = split_line[0]
                if not migrate_v05 and key.startswith("walk_through"):
                    migrate_v05 = True

                value = split_line[1]
                if (key in self.boolean_keys):
                    preferences[key] = True if int(value) > 0 else False
                elif value is not None:
                    preferences[key] = value
            
            self.hud_environment = real_hud_environment
            if migrate_v05:
                keys = list(preferences.keys())
                for key in keys:
                    if key.startswith("context_menu") or key.startswith("walk_through"):
                        del preferences[key]
            
            self.base_prefs = preferences
            
        return copy.copy(preferences)
        
    def load_preferences(self, monitor_file_path=None):
        # Copy over defaults first
        preferences = self.load_default_preferences()        
        
        file_path = self.get_main_preferences_filename()
        lines = []        
        if os.path.exists(file_path):
           fh = open(file_path, "r")
           lines.extend(fh.readlines())
           fh.close()
                              
        if monitor_file_path is not None:
           self.monitor_file_path = monitor_file_path
           if os.path.exists(monitor_file_path):
               fh = open(monitor_file_path, "r")
               lines.extend(fh.readlines())
               fh.close()

        # Clear context_menu and walk_through stuff so the new sizes can be applied
        migrate_v05 = False
        
        # Override defaults with file values
        for index,line in enumerate(lines):
            split_line = line.strip("\n").split(",", 1)
            key = split_line[0]
            if not migrate_v05 and key.startswith("walk_through"):
                migrate_v05 = True

            value = split_line[1]
            if (key in self.boolean_keys):
                preferences[key] = True if int(value) > 0 else False
            elif value is not None:
                preferences[key] = value

        if migrate_v05:
            keys = list(preferences.keys())
            for key in keys:
                if key.startswith("context_menu") or key.startswith("walk_through"):
                    del preferences[key]

        self.prefs = preferences
        if self.hud_environment == "":
            self.base_prefs = copy.copy(preferences)
        
    # Persist the preferences as a CSV for reloading between Talon sessions later
    # But only when the new preferences have changed
    def persist_preferences(self, new_preferences, force=False):
        if not self.persisting_enabled:
            return

        preferences_changed = False
        monitor_changed = False
        
        for key, value in new_preferences.items():
            if (key not in self.prefs or value != self.prefs[key]):
                if key.endswith(self.monitor_related_pref_endings):
                    monitor_changed = True
                else:
                    preferences_changed = True
            self.prefs[key] = value
        
        if preferences_changed or force:
            self.save_preferences_file(self.get_main_preferences_filename())
        
        if (monitor_changed or force) and self.monitor_file_path is not None:
            self.save_preferences_file(self.monitor_file_path)

    def get_main_preferences_filename(self, without_hud_environment = False):
        hud_environment = self.hud_environment
        talon_hud_environment = "" if without_hud_environment or hud_environment == None or hud_environment == "" else hud_environment + "_"
        return os.path.join(user_preferences_file_dir, talon_hud_environment + widget_settings_file_ending)

    # Save the given preferences file
    def save_preferences_file(self, filename):
        is_monitor_preference = filename != self.get_main_preferences_filename()

        # Transform data before persisting
        lines = []
        for index, key in enumerate(self.prefs):
            if ( is_monitor_preference and key.endswith(self.monitor_related_pref_endings) ) or \
                ( not is_monitor_preference and not key.endswith(self.monitor_related_pref_endings) ):
                
                # Skip persisting the initial current topics if the file does not exist yet to allow
                # The topics to by migrated properly instead of being cleared on the first load
                if key.endswith("_current_topics") and not os.path.exists(filename):
                    continue
                
                # Skip values that are the same in the base environment preferences
                # To keep the changes as specific as possible to each environment
                # Unless they are content related
                if self.hud_environment != "" and not key.endswith("_current_topics") and key in self.base_prefs and self.base_prefs[key] == self.prefs[key]:
                    continue
                
                value = self.prefs[key]
                transformed_value = value
                line = key + ","
                if (key in self.boolean_keys):
                    transformed_value = "1" if value else "0"
                elif value is None:
                    continue
                line = line + transformed_value
                
                # Only add new lines to non-final rows
                if index + 1 != len(self.prefs):
                    line = line + "\n"
                lines.append(line)

        if len(lines) > 0:
            fh = open(filename, "w")
            fh.write("".join(lines))
            fh.close()
