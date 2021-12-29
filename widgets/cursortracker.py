from user.talon_hud.base_widget import BaseWidget
from user.talon_hud.utils import hit_test_rect
from user.talon_hud.content.typing import HudScreenRegion
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from talon import skia, ui, cron, ctrl
from talon.types.point import Point2d
import time
import numpy

class HeadUpCursorTracker(BaseWidget):

    # In this widget the limit_* variables are used to determine the size and distance from the pointer

    allowed_setup_options = ["position", "dimension"]
    mouse_enabled = False
    soft_enabled = False
    mouse_poller = None
    prev_mouse_pos = None
    smooth_mode = True

    preferences = HeadUpDisplayUserWidgetPreferences(type="cursor_tracker", x=15, y=15, width=15, height=15, enabled=True, sleep_enabled=False)
    subscribed_content = [
        "mode",
        "screen_regions"
    ]
    
    active_icon = None
    cursor_icons = []
    content = {
        'mode': 'command',
        "screen_regions": {
           "cursor": []
        }
    }        
    
    def refresh(self, new_content):
        if ("mode" in new_content and new_content["mode"] != self.content['mode']):
            if (new_content["mode"] == 'sleep'):
                self.soft_disable()
            else:
                self.soft_enable()

        if "screen_regions" in new_content and "cursor" in new_content["screen_regions"]:
            self.update_icons(new_content["screen_regions"]["cursor"])

    def enable(self, persist=False):
        if not self.enabled:
            self.previous_pos = ctrl.mouse_pos()
            self.determine_active_icon(self.previous_pos)
            super().enable(persist)
            self.soft_enable()
    
    def disable(self, persist=False):
        if self.enabled:
            self.soft_disable()
            super().disable(persist)
    
    def soft_enable(self):
        if not self.soft_enabled:
            self.soft_enabled = True
            self.mouse_poller = cron.interval('30ms', self.poll_mouse_pos)
            self.canvas.resume()
            
    def soft_disable(self):
        if self.soft_enabled:
            self.soft_enabled = False
            cron.cancel(self.mouse_poller)
            self.mouse_poller = None
            self.canvas.resume()
            
    def update_icons(self, cursor_icons: list[HudScreenRegion] = None):
        soft_enable = False    
        if cursor_icons != None:
            new_icons = cursor_icons          
            soft_enable = self.cursor_icons != new_icons and len(new_icons) > 0
            self.cursor_icons = new_icons
        
        if self.cursor_icons:
            if soft_enable:
                self.soft_enable()
        else:
            self.soft_disable()
    
    def poll_mouse_pos(self):
        if self.canvas:
            pos = ctrl.mouse_pos()
            distance_threshold = 0.5 if self.smooth_mode else 20
            if (self.prev_mouse_pos is None or numpy.linalg.norm(numpy.array(pos) - numpy.array(self.prev_mouse_pos)) > distance_threshold):
                self.prev_mouse_pos = pos
                
                if self.setup_type == "":
                    self.x = pos[0] + self.limit_x
                    self.y = pos[1] + self.limit_y
                    self.canvas.move(self.x, self.y)
                    
                    self.determine_active_icon(pos)
                    self.canvas.freeze()
    
    # Determine the active icon based on the region the icon is in
    # If multiple regions overlap, choose the smaller more specific one
    def determine_active_icon(self, pos):
        pos = Point2d(pos[0], pos[1])    
        active_icon = None
        size = None
        for icon in self.cursor_icons:
            if icon.rect is None and active_icon is None:
                active_icon = icon
            if icon.rect is not None and hit_test_rect(icon.rect, pos):            
                if size is None or size > icon.rect.width * icon.rect.height:
                    size = icon.rect.width * icon.rect.height
                    active_icon = icon
        
        self.active_icon = active_icon
    
    def draw(self, canvas) -> bool:
        paint = self.draw_setup_mode(canvas)
        if self.soft_enabled and self.active_icon:
            self.draw_icon(canvas, self.x, self.y, self.width, paint, self.active_icon)
        return False
        
    def draw_icon(self, canvas, origin_x, origin_y, diameter, paint, icon ):
        radius = diameter / 2
        if icon.colour is not None:
            paint.color = icon.colour
            canvas.draw_circle( origin_x + radius, origin_y + radius, radius, paint)
        
        if (icon.icon is not None and self.theme.get_image(icon.icon) is not None ):
            image = self.theme.get_image(icon.icon, diameter, diameter)
            canvas.draw_image(image, origin_x + radius - image.width / 2, origin_y + radius - image.height / 2 )                

    def start_setup(self, setup_type, mouse_position = None):
        """Starts a setup mode that is used for moving, resizing and other various changes that the user might setup"""    
        if (mouse_position is not None):
            self.drag_position = [mouse_position[0] - self.limit_x, mouse_position[1] - self.limit_y]
        
        if (setup_type not in self.allowed_setup_options and setup_type not in ["", "cancel", "reload"] ):
            return
            
        pos = ctrl.mouse_pos()
        
        # Persist the user preferences when we end our setup
        if (self.setup_type != "" and not setup_type):
            self.drag_position = []
            rect = self.canvas.rect
            
            if (self.setup_type == "position"):
                self.preferences.limit_x =  int(rect.x) - pos[0]
                self.preferences.limit_y = int(rect.y) - pos[1]
                self.limit_x = self.preferences.limit_x
                self.limit_y = self.preferences.limit_y
                
            elif (self.setup_type == "dimension"):
                self.limit_x = self.preferences.limit_x
                self.limit_y = self.preferences.limit_y                
                self.width = int(rect.width)
                self.height = int(rect.height)         
                self.limit_width = int(rect.width)
                self.limit_height = int(rect.height)
                self.preferences.width = self.limit_width
                self.preferences.height = self.limit_height
                self.preferences.limit_width = self.limit_width
                self.preferences.limit_height = self.limit_height
            
            self.setup_type = setup_type
            self.preferences.mark_changed = True
            self.canvas.resume()
            self.event_dispatch.request_persist_preferences()
        # Cancel every change
        else:
            self.x = pos[0]
            self.y = pos[1]
            self.canvas.move(self.x, self.y)
            self.canvas.resume()
            super().start_setup(setup_type, mouse_position)
                
    def setup_move(self, pos):
        """Responds to global mouse movements when a widget is in a setup mode"""
        if (self.setup_type == "position"):
            pass
        elif (self.setup_type in ["dimension", "limit", "font_size"] ):
            super().setup_move(pos)
