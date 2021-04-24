from talon import Context, Module, actions, app, skia, cron, ctrl, scope, canvas, registry, settings, ui
from talon.types import Point2d
from abc import ABCMeta
import numpy
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences

class BaseWidget(metaclass=ABCMeta):
    id = None
    x = None
    y = None
    width = None
    height = None
    canvas = None
    cleared = True
    enabled = False
    theme = None
    preferences = None
    subscribed_content = ['mode']
    subscribed_logs = []
    content = {}
        
    animation_tick = 0
    animation_max_duration = 100
    
    setup_type = ""
    setup_vertical_direction = ""
    setup_horizontal_direction = ""
    
    def __init__(self, id, preferences_dict, theme):
        self.id = id
        self.theme = theme
        self.load(preferences_dict)
        self.load_theme_values()
            
    # Load the widgets preferences
    def load(self, dict, initialize = True):
        self.preferences.load(self.id, dict)
        self.sleep_enabled = self.preferences.sleep_enabled
        self.show_animations = self.preferences.show_animations
        self.x = self.preferences.x
        self.y = self.preferences.y
        self.width = self.preferences.width
        self.height = self.preferences.height
        self.limit_x = self.preferences.limit_x
        self.limit_y = self.preferences.limit_y
        self.limit_width = self.preferences.limit_width
        self.limit_height = self.preferences.limit_height        
        self.font_size = self.preferences.font_size
        self.alignment = self.preferences.alignment
        self.expand_direction = self.preferences.expand_direction
        
        if (initialize and self.preferences.enabled):
            self.enable()        
    
    def set_theme(self, theme):
        self.theme = theme
        if self.enabled:
            self.load_theme_values()
            self.canvas.resume()
            self.animation_tick = self.animation_max_duration if self.show_animations else 0
    
    def update_content(self, content):
        if not self.sleep_enabled and "mode" in content and content["mode"] == "sleep":
            self.disable()
    
        self.refresh(content)
        for key in content:
            self.content[key] = content[key]
        
        if self.enabled:
            self.canvas.resume()
    
    def enable(self, persisted=False):
        if not self.enabled:
            self.enabled = True
            self.canvas = canvas.Canvas(min(self.x, self.limit_x), min(self.y, self.limit_y), max(self.width, self.limit_width), max(self.height, self.limit_height))
            self.canvas.register('draw', self.draw_cycle)
            self.animation_tick = self.animation_max_duration if self.show_animations else 0
            self.canvas.resume()
            
            if persisted:
                self.preferences.enabled = True
                self.preferences.mark_changed = True
                actions.user.persist_hud_preferences()
            self.cleared = False
            
    def disable(self, persisted=False):
        if self.enabled:
            self.enabled = False
            self.animation_tick = -self.animation_max_duration if self.show_animations else 0
            self.canvas.resume()
            
            if persisted:
                self.preferences.enabled = False
                self.preferences.mark_changed = True
                actions.user.persist_hud_preferences()
                
            self.cleared = False
            self.start_setup("cancel")

    def set_preference(self, preference, value, persisted=False):
        dict = {}
        dict[self.id + "_" + preference] = value
        self.load(dict, False)
        if self.enabled:
            self.canvas.resume()
        
        if persisted:
            self.preferences.mark_changed = True
            actions.user.persist_hud_preferences()            
            
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
    
    def draw_setup_mode(self, canvas) -> skia.Paint:
        """Implements drawing the dimension lines when resizing elements"""    
        paint = canvas.paint
        if self.setup_type in ["dimension", "limit", "position"]:
            # Colours blue and red chosen for contrast and decreased possibility of colour blindness making it difficult
            # To make out the width and the limit lines
            paint.color = '0000AA'
            resize_margin = 2
            leftmost = self.x + resize_margin
            rightmost = self.x + self.width - resize_margin
            topmost = self.y + resize_margin
            bottommost = self.y + self.height - resize_margin
            canvas.draw_line(leftmost, topmost, rightmost, topmost)
            canvas.draw_line(rightmost, topmost, rightmost, bottommost)
            canvas.draw_line(rightmost, bottommost, leftmost, bottommost)
            canvas.draw_line(leftmost, bottommost, leftmost, topmost)
            
            paint.color = 'FF0000'
            resize_margin = 0
            leftmost = self.limit_x + resize_margin
            rightmost = self.limit_x + self.limit_width - resize_margin
            topmost = self.limit_y + resize_margin
            bottommost = self.limit_y + self.limit_height - resize_margin
            canvas.draw_line(leftmost, topmost, rightmost, topmost)
            canvas.draw_line(rightmost, topmost, rightmost, bottommost)
            canvas.draw_line(rightmost, bottommost, leftmost, bottommost)
            canvas.draw_line(leftmost, bottommost, leftmost, topmost)
        return paint    
    
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
            horizontal_diff = x - self.limit_x
            vertical_diff = y - self.limit_y
            self.limit_x = x
            self.limit_y = y
            
            self.x = self.x + horizontal_diff
            self.y = self.y + vertical_diff
            
            self.canvas.move(x, y)            
            self.canvas.resume()
        elif (self.setup_type in ["dimension", "limit", "font_size"] ):
            x, y = pos
            
            # Determine the origin point of the widget which we should use for distance calculation with the current mouse position
            # Use the top right point if our mouse is to the bottom left of the widget and so on for every direction
            current_origin = Point2d(self.x, self.y)
            if (self.setup_horizontal_direction == "left"):
                current_origin.x = self.x + self.width
            if (self.setup_vertical_direction == "up"):
                current_origin.y = self.y + self.height
                
            total_direction = Point2d(x - current_origin.x, y - current_origin.y)
            
            # There is a slight jitter when dealing with canvas resizes, maybe we should set the canvas as big as possible and just do drawing instead
            if (self.setup_type in ["dimension", "limit"]):
                canvas_width = abs(total_direction.x)
                canvas_height = abs(total_direction.y)
                
                if (self.setup_type == "dimension"):
                    canvas_x = x if self.setup_horizontal_direction == "left" else self.x
                    canvas_y = y if self.setup_vertical_direction == "up" else self.y
                    self.x = canvas_x
                    self.y = canvas_y
                    self.width = canvas_width
                    self.height = canvas_height
                    self.limit_x = canvas_x
                    self.limit_y = canvas_y
                    self.limit_width = canvas_width
                    self.limit_height = canvas_height                    
                    rect = ui.Rect(canvas_x, canvas_y, canvas_width, canvas_height)
                elif (self.setup_type == "limit"):
                    canvas_x = min(x, self.x) if self.setup_horizontal_direction == "left" else self.x
                    canvas_y = min(y, self.y) if self.setup_vertical_direction == "up" else self.y
                    self.limit_x = canvas_x
                    self.limit_y = canvas_y
                    self.limit_width = max(self.width, canvas_width)
                    self.limit_height = max(self.height, canvas_height)
                    
                    rect = ui.Rect(canvas_x, canvas_y, self.limit_width, self.limit_height  )
            
                self.canvas.set_rect(rect)
            elif (self.setup_type == "font_size"):
                total_distance = numpy.linalg.norm(numpy.array(total_direction))
                
                # This number is tested using the distance from the corner of the screen to the opposite corner, which is slightly more than 2000 pixels on a 1920*1080 screen
                # Aiming for a rough max font size of about 72
                scale_multiplier = 0.033
                self.font_size = max(8, int(total_distance * scale_multiplier ))
            self.canvas.resume()
        
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
            rect = self.canvas.get_rect()
            
            if (self.setup_type == "position"):
                self.preferences.x = int(rect.x) if self.limit_x == self.x else int(rect.x - ( self.limit_x - self.x ))
                self.preferences.y = int(rect.y) if self.limit_y == self.y else int(rect.y - ( self.limit_y - self.y ))
                self.preferences.limit_x = int(rect.x)
                self.preferences.limit_y = int(rect.y)
            elif (self.setup_type == "dimension"):
                self.preferences.x = int(rect.x)
                self.preferences.y = int(rect.y)
                self.preferences.width = int(rect.width)
                self.preferences.height = int(rect.height)
                self.preferences.limit_x = int(rect.x)
                self.preferences.limit_y = int(rect.y)
                self.preferences.limit_width = int(rect.width)
                self.preferences.limit_height = int(rect.height)
            elif (self.setup_type == "limit" ):
                self.preferences.x = self.x
                self.preferences.y = self.y
                self.preferences.width = self.width
                self.preferences.height = self.height
                self.preferences.limit_x = int(rect.x)
                self.preferences.limit_y = int(rect.y)
                self.preferences.limit_width = int(rect.width)
                self.preferences.limit_height = int(rect.height)
            elif (self.setup_type == "font_size" ):
                self.preferences.font_size = self.font_size
            
            self.setup_type = setup_type
            
            self.preferences.mark_changed = True
            self.canvas.resume()
            actions.user.persist_hud_preferences()
        # Cancel every change
        elif setup_type == "cancel":
            if (self.setup_type != ""):
                self.load({}, False)
                
                if self.canvas:
                    rect = ui.Rect(self.x, self.y, self.width, self.height)                    
                    self.canvas.set_rect(rect)
                
                self.setup_type = ""
        # Start the setup state
        elif self.setup_type != setup_type:
            self.setup_type = setup_type
            x, y = ctrl.mouse_pos()
            
            center_x = self.x + ( self.width / 2 )
            center_y = self.y + ( self.height / 2 )
            
            # Determine the direction of the mouse from the widget
            direction = Point2d(x - center_x, y - center_y)
            self.setup_horizontal_direction = "left" if direction.x < 0 else "right"
            self.setup_vertical_direction = "up" if direction.y < 0 else "down"            

            if (self.setup_type != ""):
                self.mouse_move(ctrl.mouse_pos())