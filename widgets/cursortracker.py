from user.talon_hud.base_widget import BaseWidget
from talon import skia, ui, Module, cron, actions, ctrl
import time
import numpy
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences

class HeadUpCursorTracker(BaseWidget):

    allowed_setup_options = ["position", "dimension", "font_size"]
    mouse_enabled = False
    soft_enabled = False
    mouse_poller = None
    prev_mouse_pos = None    
    smooth_mode = False

    preferences = HeadUpDisplayUserWidgetPreferences(type="cursor_tracker", x=0, y=0, width=10, height=10, enabled=True, sleep_enabled=False)
    subscribed_content = [
        "mode"
    ]
    
    active_icon = None
    cursor_icons = [{
                'image': 'de_DE',
                'rect': None
            }]
    content = {
        'mode': 'command',
        'cursor_icons': [
            {
                'image': 'de_DE',
                'rect': None
            }
        ]
    }        
    
    def refresh(self, new_content):
        if ("mode" in new_content and new_content["mode"] != self.content['mode']):
            if (new_content["mode"] == 'sleep'):
                self.soft_disable()
            else:
                self.soft_enable()

        if "cursor_icons" in new_content:
            self.update_icons(new_content['cursor_icons'])

    def enable(self, persist=False):
        if not self.enabled:
            self.previous_pos = ctrl.mouse_pos()
            self.determine_active_icon()
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
            
    def update_icons(self, cursor_icons = None):
        soft_enable = False    
        if cursor_icons != None:
            new_icons = []
            for cursor_icon in cursor_icons:
                new_icons.append({'image': cursor_icon['image'], 
                    'colour': cursor_icon['colour'] if 'colour' in cursor_icon else None, 
                    'rect': cursor_icon['rect'] if 'rect' in cursor_icon else None})
          
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
                self.x = pos[0] + 20
                self.y = pos[1] + 20
                self.limit_x = pos[0] + 20
                self.limit_y = pos[1] + 20
                self.canvas.move(pos[0] + 20, pos[1] + 20)
                
                self.determine_active_icon()
                self.canvas.freeze()        
    
    def determine_active_icon(self):    
        # TODO determine based on active region
        if self.cursor_icons:
            self.active_icon = self.cursor_icons[0]
        else:
            self.active_icon = None
    
    def draw(self, canvas) -> bool:
        paint = self.draw_setup_mode(canvas)
        if self.soft_enabled and self.active_icon:
            self.draw_icon(canvas, self.x, self.y, self.width, paint, self.active_icon)
        return False
        
    def draw_icon(self, canvas, origin_x, origin_y, diameter, paint, icon ):
        radius = diameter / 2
        canvas.draw_circle( origin_x + radius, origin_y + radius, radius, paint)
        if (icon['image'] is not None and self.theme.get_image(icon['image']) is not None ):
            image = self.theme.get_image(icon['image'], diameter, diameter)
            canvas.draw_image(image, origin_x + radius - image.width / 2, origin_y + radius - image.height / 2 )                
