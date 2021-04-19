from talon import Context, Module, actions, app, skia, cron, ctrl, scope, canvas, registry, settings, ui
from abc import ABCMeta
import numpy

class BaseWidget(metaclass=ABCMeta):
    id = None
    x = None
    y = None
    width = None
    height = None
    canvas = None
    cleared = True
    enabled = False
    setup_type = ""
    theme = None
    preferences = None
    subscribed_content = ['mode']
    subscribed_logs = []
    content = {}
        
    animation_tick = 0
    animation_max_duration = 100
    
    def __init__(self, id, preferences, theme):
        self.id = id
        self.preferences = preferences
        self.theme = theme
        self.x = self.preferences.prefs[id + '_x']
        self.y = self.preferences.prefs[id + '_y']
        self.width = self.preferences.prefs[id + '_width']
        self.height = self.preferences.prefs[id + '_height']
        self.load_theme_values()        
    
    def set_theme(self, theme, animated=True):
        self.theme = theme
        if self.enabled:
            self.load_theme_values()
            self.canvas.resume()            
            self.animation_tick = self.animation_max_duration if animated else 0
    
    def update_content(self, content, animated=True):
        self.refresh(content, animated)
        for key in content:
            self.content[key] = content[key]
        
        if self.enabled:
            self.canvas.resume()
    
    def enable(self, animated=True):
        if not self.enabled:
            self.enabled = True
            self.canvas = canvas.Canvas(self.x, self.y, self.width, self.height)
            self.canvas.register('draw', self.draw_cycle)
            self.animation_tick = self.animation_max_duration if animated else 0
            self.canvas.resume()
            self.preferences.persist_preferences({self.id + '_enabled': True})
            self.cleared = False
            
    def disable(self, animated=True):
        if self.enabled:
            self.enabled = False
            self.animation_tick = -self.animation_max_duration if animated else 0
            self.canvas.resume()
            self.preferences.persist_preferences({self.id + '_enabled': False})
            self.cleared = False
            # TODO CANCEL SETUP MODE
            
    # Clear up all the resources after a disabling
    def clear(self):
        if (self.canvas is not None):
            self.canvas.unregister('draw', self.draw_cycle)
            self.canvas.close()
            self.canvas = None
            self.cleared = True

    # Central drawing cycle attached to the canvas
    def draw_cycle(self, canvas):
        continue_drawing = False 
        
        if self.animation_tick != 0:
            # Send ticks to the animation method
            if (self.animation_tick < 0):
                self.animation_tick = self.animation_tick + 1
            elif (self.animation_tick > 0 ):
                self.animation_tick = self.animation_tick - 1
            
            animation_tick = self.animation_tick if self.animation_tick >= 0 else self.animation_max_duration - abs(self.animation_tick)
            continue_drawing = self.draw_animation(canvas, animation_tick) if self.animation_tick != 0 else True
        else:
            continue_drawing = self.draw(canvas)
            
        if not continue_drawing:
            self.canvas.pause()
            self.animation_tick = 0
            if not self.enabled:
                self.clear()
    
    def draw(self, canvas) -> bool:
        """Implement your canvas drawing logic here, returning False will stop the rendering, returning True will continue it"""
        return False
        
    def draw_animation(self, canvas, animation_tick) -> bool:
        """Implement your canvas animation drawing logic here, returning False will stop the rendering, returning True will continue it"""
        return False
    
    def refresh(self, new_content):
        """Implement your state changing logic here, for example, when a mode is changed"""
        pass
    
    def mouse_move(self, pos):
        """Mouse move events will be sent here whenever they change to update the UI if neccesary"""
        if (self.setup_type == "position"):
            x, y = pos
            self.canvas.move(x, y)
        
    def click(self, pos):
        """Responds to click or dwell actions"""
        # Confirm the setup
        if (self.setup_type != None):
            self.start_setup(None)
        
    def load_theme_values(self):
        """Respond to theme load ins here"""    
        pass
        
    def start_setup(self, setup_type):
        """Starts a setup mode that is used for moving, resizing and other various changes that the user might setup"""
        # Persist the user preferences when we end our setup
        if (self.setup_type != "" and not setup_type):
            self.setup_type = setup_type

            rect = self.canvas.get_rect()
            self.x = int(rect.x)
            self.y = int(rect.y)
            self.width = int(rect.width)
            self.height = int(rect.height)
            
            self.preferences.persist_preferences({
                self.id + '_x': self.x,
                self.id + '_y': self.y,
                self.id + '_width': self.width,
                self.id + '_height': self.height
            })
            
        # Start the setup state
        elif self.setup_type != setup_type:
            self.setup_type = setup_type
            if (self.setup_type == "position"):
                x, y = ctrl.mouse_pos()
                self.canvas.move(x, y)