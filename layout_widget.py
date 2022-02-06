from talon import canvas, ui
from .base_widget import BaseWidget
from .utils import layout_rich_text
from .content.typing import HudContentPage, HudPanelContent
from random import randint

class LayoutWidget(BaseWidget):
    """This widget has a layout pass and changes the mouse capture area based on the content
    The extra canvas is used to make sure the drawing doesn't flicker when the content changes
    """
    
    default_buttons = []
    buttons = []
    
    mark_layout_invalid = True
    mouse_capture_canvas: canvas.Canvas
    layout = []
    page_index = 0
    
    def enable(self, persisted=False):
        if not self.enabled:
            self.enabled = True
        
            if self.panel_content.content[0]:
                self.generate_canvases()
            
            if persisted:
                self.preferences.enabled = True
                self.preferences.mark_changed = True
                self.event_dispatch.request_persist_preferences()
            self.cleared = False
            
    def generate_canvases(self):
        if self.mouse_enabled:
            self.mouse_capture_canvas = canvas.Canvas(min(self.x, self.limit_x), min(self.y, self.limit_y), max(self.width, self.limit_width), max(self.height, self.limit_height))            
            self.mouse_capture_canvas.blocks_mouse = True
            self.mouse_capture_canvas.register('mouse', self.on_mouse)
            self.mouse_capture_canvas.freeze()
        
        # Copied over from base widget enabled to make sure blocks_mouse setting isn't changed
        self.canvas = canvas.Canvas(min(self.x, self.limit_x), min(self.y, self.limit_y), max(self.width, self.limit_width), max(self.height, self.limit_height))
        self.canvas.register('draw', self.draw_cycle)
        self.animation_tick = self.animation_max_duration if self.show_animations else 0
        self.canvas.resume()        
            
    def disable(self, persisted=False):
        if self.enabled:
            if self.mouse_enabled and self.mouse_capture_canvas:
                self.mouse_capture_canvas.blocks_mouse = False
                self.mouse_capture_canvas.unregister('mouse', self.on_mouse)
                self.mouse_capture_canvas = None
        
            # Copied over from base widget disable to make sure blocks_mouse setting isn't changed        
            self.enabled = False
            self.animation_tick = -self.animation_max_duration if self.show_animations else 0
            if self.canvas:
                self.canvas.resume()
            
            if persisted:
                self.preferences.enabled = False
                self.preferences.mark_changed = True
                self.event_dispatch.request_persist_preferences()
                
            self.cleared = False
            self.start_setup("cancel")
    
    def refresh(self, new_content):
        self.mark_layout_invalid = True
        
    def content_handler(self, event) -> bool:
        if isinstance(event.content, HudPanelContent):
            return self.update_panel(event.content)
        else:
            return super().content_handler(event)

    def set_page_index(self, page_index: int):
        self.page_index = max(0, min(page_index, len(self.layout) - 1))
        if self.canvas:
            self.start_setup("")        
            self.mark_layout_invalid = True
            self.canvas.resume()
            
    def get_content_page(self) -> HudContentPage:
        current = self.page_index + 1
        total = max(1, len(self.layout) if self.layout else 1)
        percent = current / total
        return HudContentPage(current, total, percent)
        
    def start_setup(self, setup_type, mouse_position = None):
        if not self.canvas:
            return    
    
        self.mark_layout_invalid = True
        
        # Make sure the canvas is still the right size after canceling resizing
        if setup_type == "cancel":
            self.drag_position = []  
            if (self.setup_type != ""):
                self.load({}, False)
                self.setup_type = ""
                if self.canvas:
                    self.canvas.rect = ui.Rect(self.limit_x, self.limit_y, self.limit_width, self.limit_height)
                    self.canvas.resume()
        elif setup_type == "reload":
            self.drag_position = []  
            self.setup_type = ""
            if self.canvas:
                # Only do a rect change if it has actually changed to prevent costly operations
                if self.canvas.rect.x != self.limit_x or self.canvas.rect.y != self.limit_y or \
                    self.canvas.rect.width != self.limit_width or self.canvas.rect.height != self.limit_height:
                    self.canvas.rect = ui.Rect(self.limit_x, self.limit_y, self.limit_width, self.limit_height)
                self.canvas.resume()
        else:
            super().start_setup(setup_type, mouse_position)

    def setup_move(self, pos):
        if not self.canvas:
            return
        self.mark_layout_invalid = True
        super().setup_move(pos)

    def update_panel(self, panel_content) -> bool:
        if not panel_content.content[0] and self.enabled:
            self.disable()

        if not self.enabled and panel_content.show:
            self.panel_content = panel_content        
            self.enable(True)
        
        if self.enabled:
            self.panel_content = panel_content
            self.current_topics = [panel_content.topic]
            self.mark_layout_invalid = True
            if not self.canvas:
                self.generate_canvases()
            self.canvas.resume()
        return self.enabled and panel_content.topic in self.current_topics
        

    def layout_content(self, canvas, paint):
        # Determine the dimensions and positions of the content
        return [{"rect": ui.Rect(self.limit_x, self.limit_y, self.limit_width, self.limit_height)}]
        
    def draw_content(self, canvas, paint, dimensions) -> bool:
        # Draw the content using the layout given dimensions
        return False
        
    def draw(self, canvas) -> bool:
        paint = self.draw_setup_mode(canvas)
        
        if self.mark_layout_invalid:
            self.layout = self.layout_content(canvas, paint)
            
        if self.page_index > len(self.layout) - 1:
            self.page_index = len(self.layout) -1
        content_dimensions = self.layout[self.page_index]
        
        # Debug layout size / position
        #paint.color = "00FF00"
        #paint.style = paint.Style.STROKE
        #canvas.draw_rect(self.capture_rect)
        
        continue_drawing = self.draw_content(canvas, paint, content_dimensions)
        
        # Automatically resize the canvas based on the content to make sure no dead zones 
        # will show up when clicking in or near the text panel
        if self.setup_type == "":
            if self.mark_layout_invalid and self.mouse_capture_canvas:
                self.resize_mouse_canvas(content_dimensions)
        return continue_drawing
    
    def resize_mouse_canvas(self, content_dimensions):
        rect = content_dimensions["rect"]
        self.capture_rect = rect
        self.mouse_capture_canvas.rect = rect
        self.mouse_capture_canvas.freeze()
        self.mark_layout_invalid = False
        
        
    def draw_rich_text(self, canvas, paint, rich_text, x, y, line_padding, single_line=False):
        # Draw text line by line
        text_colour = paint.color
        error_colour = self.theme.get_colour('error_colour', 'AA0000')
        warning_colour = self.theme.get_colour('warning_colour', 'F75B00')
        success_colour = self.theme.get_colour('success_colour', '00CC00')
        info_colour = self.theme.get_colour('info_colour', '30AD9E')
    
        current_line = -1
        for index, text in enumerate(rich_text):
            paint.font.embolden = "bold" in text.styles
            paint.font.skew_x = -0.33 if "italic" in text.styles else 0
            paint.color = text_colour
            if "warning" in text.styles:
                paint.color = warning_colour
            elif "success" in text.styles:
                paint.color = success_colour
            elif "error" in text.styles:
                paint.color = error_colour
            elif "notice" in text.styles:
                paint.color = info_colour
                        
            current_line = current_line + 1 if text.x == 0 else current_line
            if single_line and current_line > 0:
                return
            
            if text.x == 0:
                y += paint.textsize
                if index != 0:
                    y += line_padding
            
            
            # Keep this debugging code in here in case we need to test sizes again
            #paint_colour = paint.color
            #paint.color = self.get_random_colour() + "DD"
            #canvas.draw_rect( ui.Rect(x + text.x, y + text.y, text.width, paint.textsize) )            
            #paint.color = paint_colour
            canvas.draw_text(text.text, x + text.x, y )

    def get_random_colour(self):    
        red = randint(180, 255)
        green = randint(180, 255)
        blue = randint(180, 255)
        
        red_hex = '0' + format(red, 'x') if red <= 15 else format(red, 'x')
        green_hex = '0' + format(green, 'x') if green <= 15 else format(green, 'x')
        blue_hex = '0' + format(blue, 'x') if blue <= 15 else format(blue, 'x')
        return red_hex + green_hex + blue_hex
        
