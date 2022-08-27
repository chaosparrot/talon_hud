from talon import skia, cron, ctrl, scope, canvas, ui
from talon.types import Point2d
from abc import ABCMeta
import numpy
from .widget_preferences import HeadUpDisplayUserWidgetPreferences
from .content.partial_content import HudPartialContent
import copy

class BaseWidget(metaclass=ABCMeta):
    id = None
    canvas = None
    cleared = True
    enabled = False
    theme = None
    event_dispatch = None
    preferences = None
    
    mouse_enabled = False
    
    # Position dragging position offset - Used in manual dragging
    drag_position = []
    
    # Context menu buttons if applicable
    buttons = []
    
    allowed_setup_options = ["position", "dimension", "limit", "font_size"]
    
    # New content topic types
    topic_types = []
    current_topics = []
    content = None
        
    animation_tick = 0
    animation_max_duration = 100
    
    setup_type = ""
    setup_vertical_direction = ""
    setup_horizontal_direction = ""
    
    def __init__(self, id, preferences_dict, theme, event_dispatch, subscriptions = None, current_topics = None):
        self.id = id
        self.theme = theme
        self.preferences = copy.copy(self.preferences)
        self.event_dispatch = event_dispatch

        if subscriptions != None:
            self.subscriptions = subscriptions
        if current_topics != None:
            self.current_topics = current_topics

        self.content = HudPartialContent(self.topic_types)
        self.content.set_persisted_topics(self.current_topics)
        self.preferences.current_topics = self.current_topics

        self.load(preferences_dict)

    # Load the widgets preferences
    def load(self, dict, initialize = True, update_enabled = False):
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
        self.minimized = self.preferences.minimized
        self.subscriptions = self.preferences.subscriptions
        if self.preferences.current_topics is not None:
            self.current_topics = self.preferences.current_topics
            self.content.set_persisted_topics(self.preferences.current_topics)
        self.load_extra_preferences()
        
        # For re-enabling or disabling widgets after a reload ( mostly for talon hud environment changes )
        if update_enabled:
            if self.enabled != self.preferences.enabled:
                if "enabled" in dict and dict["enabled"]:            
                    self.show_animations = False
                    self.enable() if self.preferences.enabled else self.disable()
                    self.show_animations = self.preferences.show_animations

        if initialize:
            self.load_theme_values()        
    
    def load_extra_preferences(self):
        """
        To be overridden by derived types to load widget-specific preferences
        """
        pass
    
    # Clear the given topic from the current topics
    def clear_topic(self, topic: str):
        for topic_type in self.topic_types:
            self.content.remove_topic(topic_type, topic)
        self.preferences.current_topics = self.content.get_current_topics()
        self.preferences.mark_changed = True
        self.event_dispatch.request_persist_preferences()
    
    def set_theme(self, theme):
        self.theme = theme
        self.load_theme_values()
        if self.enabled:
            if self.canvas:
                self.canvas.resume()
            self.animation_tick = self.animation_max_duration if self.show_animations else 0

    def content_handler(self, event) -> bool:
        self.content.process_event(event)
        
        # Set the new content topics if they have changed
        new_topics = self.content.get_current_topics()
        if len(new_topics) != len(self.current_topics) or len(set(new_topics) - set(self.current_topics)) > 0:
            self.current_topics = new_topics
            self.preferences.current_topics = self.current_topics
            self.preferences.mark_changed = True
            self.event_dispatch.request_persist_preferences()
        
        if not self.sleep_enabled and event.topic_type == "variable" and event.topic == "mode":
            if (event.content == "sleep"):
                self.disable()
            elif self.preferences.enabled == True:
                self.enable()
        
        self.refresh({"event": event})
        
        updated = False
        if self.enabled and self.canvas:
            self.canvas.resume()
            updated = True
        return updated

    def update_panel(self, panel_content) -> bool:
        if not panel_content.content[0] and self.enabled:
            self.disable()
        
        if not self.enabled and panel_content.show:
            self.enable()
        
        if self.enabled:
            self.panel_content = panel_content
            self.canvas.resume()
        return self.enabled and panel_content.topic
    
    def enable(self, persisted=False):
        if not self.enabled:
            self.enabled = True
            self.canvas = self.generate_canvas(min(self.x, self.limit_x), min(self.y, self.limit_y), max(self.width, self.limit_width), max(self.height, self.limit_height))
            if self.mouse_enabled:
                self.canvas.blocks_mouse = True
                self.canvas.register("mouse", self.on_mouse)
            self.canvas.register("draw", self.draw_cycle)
            self.animation_tick = self.animation_max_duration if self.show_animations else 0
            self.canvas.resume()
            
            if persisted:
                self.preferences.enabled = True
                self.preferences.mark_changed = True
                self.event_dispatch.request_persist_preferences()
            self.cleared = False
                        
    def disable(self, persisted=False):
        if self.enabled:
            if self.mouse_enabled:
                self.canvas.unregister("mouse", self.on_mouse)
        
            self.enabled = False
            self.animation_tick = -self.animation_max_duration if self.show_animations else 0
            self.canvas.resume()
            
            if persisted:
                self.preferences.enabled = False
                self.preferences.mark_changed = True
                self.event_dispatch.request_persist_preferences()
                
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
            self.event_dispatch.request_persist_preferences()
            
    # Clear up all the resources after a disabling
    def clear(self):
        if (self.canvas is not None):
            self.canvas.unregister("draw", self.draw_cycle)
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
            if self.canvas:
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
            paint.color = "0000AA"
            resize_margin = 2
            leftmost = self.x + resize_margin
            rightmost = self.x + self.width - resize_margin
            topmost = self.y + resize_margin
            bottommost = self.y + self.height - resize_margin
            canvas.draw_line(leftmost, topmost, rightmost, topmost)
            canvas.draw_line(rightmost, topmost, rightmost, bottommost)
            canvas.draw_line(rightmost, bottommost, leftmost, bottommost)
            canvas.draw_line(leftmost, bottommost, leftmost, topmost)
            
            paint.color = "FF0000"
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
    
    def on_mouse(self, event):
        """This is where the mouse events get sent if mouse_enabled is set to True"""
        # Mouse dragging of elements that have mouse enabled
        if event.button == 0:
            self.event_dispatch.hide_context_menu()
            if len(self.drag_position) == 0 and event.event == "mousedown":
                self.drag_position = [event.gpos.x - self.limit_x, event.gpos.y - self.limit_y]
            elif event.event == "mouseup" and len(self.drag_position) > 0:
                self.start_setup("")
                self.drag_position = []
        if len(self.drag_position) > 0 and event.event == "mousemove":
            if self.setup_type != "position":
                self.start_setup("position")
            else:
                self.setup_move(event.gpos)
    
    def draw(self, canvas) -> bool:
        """Implement your canvas drawing logic here, returning False will stop the rendering, returning True will continue it"""
        return False
                
    def draw_animation(self, canvas, animation_tick) -> bool:
        """Implement your canvas animation drawing logic here, returning False will stop the rendering, returning True will continue it"""
        return False
    
    def refresh(self, new_content):
        """Implement your state changing logic here, for example, when a mode is changed"""
        pass
        
    def load_theme_values(self):
        """Respond to theme load ins here"""    
        pass
        
    def start_setup(self, setup_type, mouse_position = None):
        """Starts a setup mode that is used for moving, resizing and other various changes that the user might setup"""            
        if (mouse_position is not None):
            self.drag_position = [mouse_position[0] - self.limit_x, mouse_position[1] - self.limit_y]
        
        if (setup_type not in self.allowed_setup_options and setup_type not in ["", "cancel", "reload"] ):
            return
        # Persist the user preferences when we end our setup
        if (self.setup_type != "" and not setup_type):
            self.drag_position = []
            rect = self.canvas.rect
            
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
            if self.canvas:
                self.canvas.resume()
            self.event_dispatch.request_persist_preferences()
        # Cancel every change
        elif setup_type == "cancel":
            self.drag_position = []        
            if (self.setup_type != ""):
                self.load({}, False)
                
                self.setup_type = ""                
                if self.canvas and self.enabled:
                    rect = ui.Rect(self.x, self.y, self.width, self.height)                    
                    self.canvas.rect = rect
                    self.canvas.resume()
                
        elif setup_type == "reload":
            self.drag_position = []
            self.setup_type = ""             
            if self.canvas and self.enabled:
                rect = ui.Rect(self.x, self.y, self.width, self.height)
                
                # Only do a rect change if it has actually changed to prevent costly operations
                if self.canvas.rect.x != self.x or self.canvas.rect.y != self.y or \
                    self.canvas.rect.width != self.width or self.canvas.rect.height != self.height:
                    self.canvas.rect = rect
                self.canvas.resume()
                
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
                self.setup_move(ctrl.mouse_pos())
                
    def setup_move(self, pos):
        """Responds to global mouse movements when a widget is in a setup mode"""
        if not self.canvas:
            return
        
        if (self.setup_type == "position"):
            x, y = pos
            if len(self.drag_position) > 0:
                x = x - self.drag_position[0]
                y = y - self.drag_position[1]
            
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
            
                self.canvas.rect = rect
            elif (self.setup_type == "font_size"):
                total_distance = numpy.linalg.norm(numpy.array(total_direction))
                
                # This number is tested using the distance from the corner of the screen to the opposite corner, which is slightly more than 2000 pixels on a 1920*1080 screen
                # Aiming for a rough max font size of about 72
                scale_multiplier = 0.033
                self.font_size = max(8, int(total_distance * scale_multiplier ))
            self.canvas.resume()
 
    def click_button(self, button_index):
        if button_index > -1 and button_index < len(self.buttons):
            self.buttons[button_index].callback(self)

    def generate_canvas(self, x, y, width, height):
        canvas_options = {
        #    "backend": "software"
        }
        return canvas.Canvas(x, y, width, height, **canvas_options)
        
    def set_visibility(self, visible = True):
        if self.enabled:
            if self.canvas:
                if visible:
                    self.canvas.show()
                else:
                    self.canvas.hide()