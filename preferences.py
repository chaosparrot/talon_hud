import os

semantic_directory = os.path.dirname(os.path.abspath(__file__))
user_preferences_file_location =  semantic_directory + "/preferences/preferences.csv"

# Loads and persists all the data based on the users preferences
# To keep the display state consistent across sessions
class HeadUpDisplayUserPreferences:
    
    default_prefs = {
        'show_animations': True,
        'enabled': False,
        'theme_name': 'light',
    }
    
    prefs = {}
    
    boolean_keys = ['enabled', 'show_animations']
    
    def __init__(self):
        self.load_preferences()
    
    def load_preferences(self):
        if not os.path.exists(user_preferences_file_location):
            self.persist_preferences(self.default_prefs)

        fh = open(user_preferences_file_location, "r")
        lines = fh.readlines()
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
    def persist_preferences(self, new_preferences):
        changed = False
        for key, value in new_preferences.items():
            if (key not in self.prefs or value != self.prefs[key]):
                changed = True
            self.prefs[key] = value
    
        if (changed):
            fh = open(user_preferences_file_location, "w")
    
            # Transform data before persisting
            for index, key in enumerate(self.prefs):
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
                
                fh.write(line)
            fh.close() 
