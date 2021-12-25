from user.talon_hud.base_widget import BaseWidget
from user.talon_hud.utils import hit_test_rect
from user.talon_hud.content.typing import HudScreenRegion
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from talon import skia, ui, Module, cron, actions, ctrl, canvas
from talon.types.point import Point2d
import time
import numpy

class HeadUpScreenOverlay(BaseWidget):

    # In this widget the limit_width and limit_height variables are used to determine the size of the canvas

    allowed_setup_options = ["position", "dimension", "fontsize"]
    mouse_enabled = False
    soft_enabled = False
    mouse_poller = None
    prev_mouse_pos = None
    smooth_mode = True

    preferences = HeadUpDisplayUserWidgetPreferences(type="screen_overlay", x=0, y=0, width=200, height=30, enabled=True, sleep_enabled=False)
    subscribed_content = [
        "mode",
        "screen_regions"
    ]
    subscribed_topics = ['focus', 'overlay']    
    
    determine_active_regions = []
    regions = []
    active_regions = []
    canvasses = []    
    content = {
        'mode': 'command',
        "screen_regions": {
           "overlay": []
        }
    }
    
    def refresh(self, new_content):
        if ("mode" in new_content and new_content["mode"] != self.content['mode']):
            if (new_content["mode"] == 'sleep' and self.sleep_enabled == False):
                self.soft_disable()

        if "screen_regions" in new_content and "overlay" in new_content["screen_regions"]:
            self.update_regions(new_content["screen_regions"]["overlay"])

    def enable(self, persist=False):
        if not self.enabled:
            self.previous_pos = ctrl.mouse_pos()
            super().enable(persist)
            self.soft_enable()
            self.create_canvasses()
    
    def disable(self, persist=False):
        if self.enabled:
            self.soft_disable()
            super().disable(persist)
    
    def soft_enable(self):
        if not self.soft_enabled:
            self.soft_enabled = True
        self.activate_mouse_tracking()

    def soft_disable(self):
        self.clear_canvasses()    
        if self.soft_enabled:
            self.soft_enabled = False
            cron.cancel(self.mouse_poller)
            self.mouse_poller = None
            
    def update_regions(self, regions: list[HudScreenRegion] = None):
        if not self.enabled:
            self.regions = regions
            return
        
        self.active_regions = []
        soft_enable = False
        indices_to_clear = []
        region_indices_used = []
        if regions != None:
            new_regions = regions
            for index, canvas_reference in enumerate(self.canvasses):
                region_found = False
                for region_index, region in enumerate(new_regions):
                
                    # Move the canvas in case we are dealing with the same region
                    if self.compare_regions(canvas_reference['region'], region):
                        region_found = True
                        region_indices_used.append(region_index)
                        canvas_reference['canvas'].unregister('draw', canvas_reference['callback'])
                        
                        # TODO PROPER ALIGNMENT!
                        canvas_reference['canvas'].move(region.point.x, region.point.y)
                        canvas_reference['callback'] = lambda canvas, self=self, region=region: self.draw_region(canvas, region)
                        canvas_reference['region'] = region
                        canvas_reference['canvas'].register('draw', canvas_reference['callback'])
                        canvas_reference['canvas'].freeze()
                        self.canvasses[index] = canvas_reference
                
                if region_found == False:
                    indices_to_clear.append(index)
                    canvas_reference['canvas'].unregister('draw', canvas_reference['callback'])
                    canvas_reference['region'] = None
                    canvas_reference['canvas'] = None
                    canvas_reference = None
            
            soft_enable = self.regions != new_regions and len(new_regions) > 0
            self.regions = new_regions
        
        # Clear the canvasses in reverse order to make sure the indices stay correct
        indices_to_clear.reverse()
        for index in indices_to_clear:
            self.canvasses.pop(index)
        
        if self.regions:
            if soft_enable:
                self.soft_enable()
            self.activate_mouse_tracking()
            self.create_canvasses(region_indices_used)
        else:
            self.soft_disable()

    def create_canvasses(self, region_indices_used = None):
        if not region_indices_used:
            region_indices_used = []
    
        for index, region in enumerate(self.regions):
            if index not in region_indices_used:
                # TODO PROPER ALIGNMENT
                print( "REGENERATE CANVAS!" )
                canvas_reference = {'canvas': canvas.Canvas(region.point.x, region.point.y, self.limit_width, self.limit_height)}
                canvas_reference['callback'] = lambda canvas, self=self, region=region: self.draw_region(canvas, region)
                canvas_reference['region'] = region
                canvas_reference['canvas'].register('draw', canvas_reference['callback'])
                canvas_reference['canvas'].freeze()
                self.canvasses.append(canvas_reference)    
        
            
    def clear_canvasses(self):
        for canvas_reference in self.canvasses:
            if canvas_reference:
                canvas_reference['canvas'].unregister('draw', canvas_reference['callback'])
                canvas_reference['region'] = None
                canvas_reference['canvas'] = None
                canvas_reference = None
        self.canvasses = []
    
    def compare_regions(self, region_a, region_b):
        return region_a.topic == region_b.topic and region_a.colour == region_b.colour and (
            region_a.icon == region_b.icon or region_a.title == region_b.title )
    
    def activate_mouse_tracking(self):
        has_active_region = len([x for x in self.regions if x.hover_visibility]) > 0
        if not self.mouse_poller and has_active_region:
            self.mouse_poller = cron.interval('30ms', self.poll_mouse_pos)
        elif not has_active_region:
            self.active_regions = self.regions
            for canvas_reference in self.canvasses:
                canvas_reference['canvas'].freeze()
    
    def poll_mouse_pos(self):
        if self.enabled:
            pos = ctrl.mouse_pos()
            distance_threshold = 0.5 if self.smooth_mode else 20
            if (self.prev_mouse_pos is None or numpy.linalg.norm(numpy.array(pos) - numpy.array(self.prev_mouse_pos)) > distance_threshold):
                self.prev_mouse_pos = pos
                self.determine_active_regions(pos)
    
    # Determine the active regions based on the region the icon is in
    def determine_active_regions(self, pos):
        pos = Point2d(pos[0], pos[1])
        active_regions = []
        size = None
        for region in self.regions:
            if not region.hover_visibility:
                active_regions.append(region)
            else:
                if region.rect is None:
                    active_regions.append(region)
                elif region.rect is not None and region.hover_visibility == 1 and hit_test_rect(region.rect, pos):
                    active_regions.append(region)
                # For hover visibility -1 , we want the region canvas to be translucent when hovered
                # So it doesn't occlude content - But otherwise it should be visible
                elif not (region.hover_visibility == -1 and hit_test_rect(ui.Rect(region.point.x, region.point.y, self.limit_width, self.limit_height), pos)):
                        active_regions.append(region)
                        
        if self.active_regions != active_regions:
            self.active_regions = active_regions
            for canvas_reference in self.canvasses:
                canvas_reference['canvas'].freeze()
            
    
    def draw_region(self, canvas, region) -> bool:
        paint = self.draw_setup_mode(canvas)
        if self.soft_enabled:
            active = region in self.active_regions
            self.draw_icon(canvas, region.point.x, region.point.y, self.height, paint, region, active)
        
    def draw_icon(self, canvas, origin_x, origin_y, diameter, paint, region, active):
        radius = diameter / 2
        if region.colour is not None:
            paint.color = region.colour if active else self.theme.get_colour('screen_overlay_background_colour', 'F5F5F588')
            canvas.draw_circle( origin_x + radius, origin_y + radius, radius, paint)
        
        if (region.icon is not None and self.theme.get_image(region.icon) is not None ):
            image = self.theme.get_image(region.icon, diameter - 3, diameter - 3)
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
            actions.user.persist_hud_preferences()
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
