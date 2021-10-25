import os
from talon import ui

semantic_directory = os.path.dirname(os.path.abspath(__file__))
user_preferences_file_dir =  semantic_directory + "/preferences/"
old_user_preferences_file_location = user_preferences_file_dir + "preferences.csv"
user_preferences_file_location = user_preferences_file_dir + "widget_settings.csv"

# Loads and persists all the data based on the users preferences
# To keep the display state consistent across sessions
class HeadUpDisplayUserPreferences:
    
    monitor_file_path = None
    default_prefs = {
        'show_animations': True,
        'enabled': False,
        'theme_name': 'light',
    }
    
    prefs = {}
    monitor_related_pref_endings = ("_x", "_y", "_width", "_height",
        "_limit_x", "_limit_y", "_limit_width", "_limit_height",
        "_font_size", "_alignment", "_expand_direction")
    
    boolean_keys = ['enabled', 'show_animations']
    
    def __init__(self):
        self.load_preferences(self.get_screen_preferences_filepath(ui.screens()))
    
    # Get the preferences filename for the current monitor dimensions
    def get_screen_preferences_filepath(self, screens):
        preferences_title = "monitor"
        for screen in screens:
            preferences_postfix = []
            preferences_postfix.append(str(int(screen.x)))
            preferences_postfix.append(str(int(screen.y)))
            preferences_postfix.append(str(int(screen.width)))
            preferences_postfix.append(str(int(screen.height)))
            preferences_title += "(" + "_".join(preferences_postfix) + ")"
        preferences_title += ".csv"
        return user_preferences_file_dir + preferences_title
    
    def load_preferences(self, monitor_file_path=None):
        file_path = user_preferences_file_location        
        lines = []
        if os.path.exists(user_preferences_file_location):
           fh = open(file_path, "r")
           lines.extend(fh.readlines())
           fh.close()
           
        # Migration from old preferences file - Remove in a few months to allow user to migrate?
        elif os.path.exists(old_user_preferences_file_location):
           fh = open(old_user_preferences_file_location, "r")
           lines.extend(fh.readlines())
           fh.close()

        
        if monitor_file_path is not None:
           self.monitor_file_path = monitor_file_path
           if os.path.exists(monitor_file_path):
               fh = open(monitor_file_path, "r")
               lines.extend(fh.readlines())
               fh.close()
        
        # Copy over defaults first
        preferences = {}
        for key, value in self.default_prefs.items():
            preferences[key] = value
        
        # Override defaults with file values
        for index,line in enumerate(lines):
            split_line = line.strip('\n').split(',')
            key = split_line[0]
            value = split_line[1]
            if (key in self.boolean_keys):
                preferences[key] = True if int(value) > 0 else False
            elif value is not None:
                preferences[key] = value
        
        self.prefs = preferences
        
    # Persist the preferences as a CSV for reloading between Talon sessions later
    # But only when the new preferences have changed
    def persist_preferences(self, new_preferences, force=False):
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
            self.save_preferences_file(user_preferences_file_location)
        
        if (monitor_changed or force) and self.monitor_file_path is not None:
            self.save_preferences_file(self.monitor_file_path)

    # Save the given preferences file
    def save_preferences_file(self, filename):
        is_monitor_preference = filename != user_preferences_file_location

        # Transform data before persisting
        lines = []
        for index, key in enumerate(self.prefs):
            if ( is_monitor_preference and key.endswith(self.monitor_related_pref_endings) ) or \
                ( not is_monitor_preference and not key.endswith(self.monitor_related_pref_endings) ):
                value = self.prefs[key]
                transformed_value = value
                line = key + ','
                if (key in self.boolean_keys):
                    transformed_value = "1" if value else "0"
                elif value is None:
                    continue
                line = line + transformed_value
                
                # Only add new lines to non-final rows
                if index + 1 != len(self.prefs):
                    line = line + '\n'
                    lines.append(line)

        if len(lines) > 0:
            fh = open(filename, "w")                
            fh.write("".join(lines))
            fh.close()        