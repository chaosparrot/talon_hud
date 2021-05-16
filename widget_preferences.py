from typing import Dict

# Class for saving the user preferences of a specific widget
class HeadUpDisplayUserWidgetPreferences:
    # Internal, non-persisting flag to set this preference as changed for easy change detection
    mark_changed = False
        
    # The widgets type, for example statusbar
    type: str = ""
    
    # Whether or not the widget is enabled on start up and on HUD show
    enabled: bool = False
    
    # Whether or not the widget is enabled when Talon is asleep
    sleep_enabled: bool = False
    
    # Whether or not to show animations for this widget
    show_animations: bool = True
    
    # Basic positioning variables when content is smaller than the canvas size
    x:int = 0
    y:int = 0
    width:int = 0
    height:int = 0
    
    # Growth positioning variables, used when the content no longer fits in the assigned space
    # Should always be bigger or equal to the basic position variables, and be aligned to a corner to make it easy to calculate expand directions
    limit_x:int = 0
    limit_y:int = 0
    limit_width:int = 0
    limit_height:int = 0
    
    # The widgets default font size
    # Headers and other non-essential text does not neccesarily need to grow based on the widget resizing
    font_size:int = 24
    
    # Alignment of the elements
    alignment: str = "left"
    
    # Direction of initial content growth
    expand_direction: str = "down"
    
    # Initialize is purposefully kept completely optional to allow the widgets to taylor their defaults
    def __init__(self, type: str = "", enabled: bool = False, sleep_enabled: bool = False, show_animations: bool = True,
        x: int = 0, y: int = 0, width: int = 0, height:int = 0, limit_x: int = -1, limit_y: int = -1, limit_width: int = 0, limit_height:int = 0, 
        font_size: int = 24, alignment: str = "left", expand_direction:str = "down"):
        
        self.type = type
        self.enabled = enabled
        self.sleep_enabled = sleep_enabled
        self.show_animations = show_animations
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.limit_x = limit_x if limit_x >= 0 else x
        self.limit_y = limit_y if limit_y >= 0 else y
        self.limit_width = limit_width if limit_width >= width else width
        self.limit_height = limit_height if limit_height >= height else height
        
        self.font_size = font_size
        self.alignment = alignment
        self.expand_direction = expand_direction
    
    # Exports the widgets preferences as a dict useful for persisting
    def export(self, id:str) -> Dict[str, str]:
        dict = {}
        dict[id + '_type'] = self.type
        dict[id + '_enabled'] = "1" if self.enabled else "0"
        dict[id + '_sleep_enabled'] = "1" if self.sleep_enabled else "0"
        dict[id + '_show_animations'] = "1" if self.show_animations else "0"
        
        dict[id + '_x'] = str(self.x)
        dict[id + '_y'] = str(self.y)
        dict[id + '_width'] = str(self.width)
        dict[id + '_height'] = str(self.height)
        dict[id + '_limit_x'] = str(self.limit_x)
        dict[id + '_limit_y'] = str(self.limit_y)
        dict[id + '_limit_width'] = str(max(self.width, self.limit_width))
        dict[id + '_limit_height'] = str(max(self.height, self.limit_height))
        dict[id + '_font_size'] = str(self.font_size)
        dict[id + '_alignment'] = self.alignment
        dict[id + '_expand_direction'] = self.expand_direction
        
        return dict
        
    # Load the widgets preferences from a persisted format
    def load(self, id:str, persisted_dict: Dict[str, str]):
        # Display related
        if (id + "_type") in persisted_dict:
            self.type = persisted_dict[id + "_type"]
        if (id + "_enabled") in persisted_dict:
            self.enabled = int(persisted_dict[id + "_enabled"]) > 0
        if (id + "_sleep_enabled") in persisted_dict:
            self.sleep_enabled = int(persisted_dict[id + "_sleep_enabled"]) > 0
        if (id + "_show_animations") in persisted_dict:
            self.show_animations = int(persisted_dict[id + "_show_animations"]) > 0
            
        # Dimension related
        if (id + "_x") in persisted_dict:
            self.x = int(persisted_dict[id + "_x"])
        if (id + "_y") in persisted_dict:
            self.y = int(persisted_dict[id + "_y"])
        if (id + "_width") in persisted_dict:
            self.width = int(persisted_dict[id + "_width"])
        if (id + "_height") in persisted_dict:
            self.height = int(persisted_dict[id + "_height"])
        if (id + "_limit_x") in persisted_dict:
            self.limit_x = int(persisted_dict[id + "_limit_x"])
        if (id + "_limit_y") in persisted_dict:
            self.limit_y = int(persisted_dict[id + "_limit_y"])
        if (id + "_limit_width") in persisted_dict:
            self.limit_width = int(persisted_dict[id + "_limit_width"])
        if (id + "_limit_height") in persisted_dict:
            self.limit_height = int(persisted_dict[id + "_limit_height"])
            
        # Text and content related
        if (id + "_font_size") in persisted_dict:
            self.font_size = int(persisted_dict[id + "_font_size"])
        if (id + "_alignment") in persisted_dict:
            self.alignment = persisted_dict[id + "_alignment"]
        if (id + "_expand_direction") in persisted_dict:
            self.expand_direction = persisted_dict[id + "_expand_direction"]
