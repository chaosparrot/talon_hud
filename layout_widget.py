from talon import Context, Module, actions, app, skia, cron, ctrl, scope, canvas, registry, settings, ui
from talon.types import Point2d
from abc import ABCMeta
import numpy
from user.talon_hud.base_widget import BaseWidget
from user.talon_hud.utils import layout_rich_text, HudRichTextLine

class LayoutWidget(BaseWidget):
    """This widget has a layout pass and changes the mouse capture area based on the content
    The extra canvas is used to make sure the drawing doesn't flicker when the content changes
    """
    
    mark_layout_invalid = True
    mouse_capture_canvas: canvas.Canvas
    layout = []
    page_index = 0
    
    def enable(self, persisted=False):
        if not self.enabled:
            if self.mouse_enabled:
                self.mouse_capture_canvas = canvas.Canvas(min(self.x, self.limit_x), min(self.y, self.limit_y), max(self.width, self.limit_width), max(self.height, self.limit_height))            
                self.mouse_capture_canvas.blocks_mouse = True
                self.mouse_capture_canvas.register('mouse', self.on_mouse)
                self.mouse_capture_canvas.freeze()
           
            super().enable(persisted)
            self.canvas.blocks_mouse = False
            
    def disable(self, persisted=False):
        if self.enabled:
            if self.mouse_enabled:
                self.canvas.blocks_mouse = False
                self.canvas.unregister('mouse', self.on_mouse)
                self.mouse_capture_canvas.blocks_mouse = False
                self.mouse_capture_canvas.unregister('mouse', self.on_mouse)
                self.mouse_capture_canvas = None
        
            super().disable(persisted)
    
    def refresh(self, new_content):
        self.mark_layout_invalid = True
        self.page_index = 0
        
    def set_page_index(self, page_index: int):
        self.page_index = 0
        if self.canvas:
            self.canvas.resume()
        
    def setup_move(self, pos):
        self.mark_layout_invalid = True
        super().setup_move(pos)

    def update_panel(self, panel_content):
        if not panel_content.content[0] and self.enabled:
            self.disable()

        if not self.enabled and panel_content.show:
            self.enable()
    
        if self.enabled:
            self.panel_content = panel_content
            self.mark_layout_invalid = True
            self.canvas.resume()

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
        content_dimensions = self.layout[self.page_index]
        
        # Debug layout size / position
        #paint.color = "00FF00"
        #paint.style = paint.Style.STROKE
        #canvas.draw_rect(self.capture_rect)
        
        continue_drawing = self.draw_content(canvas, paint, content_dimensions)
        
        # Automatically resize the canvas based on the content to make sure no dead zones 
        # will show up when clicking in or near the text panel
        if self.setup_type == "":
            if self.mark_layout_invalid:
                rect = content_dimensions["rect"]
                self.capture_rect = rect
                self.mouse_capture_canvas.set_rect(rect)
                self.mouse_capture_canvas.freeze()
                self.mark_layout_invalid = False

        return continue_drawing
        
    def draw_rich_text(self, canvas, paint, rich_text, x, y, line_height, single_line=False):
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
            elif "info" in text.styles:
                paint.color = info_colour
            
            current_line = current_line + 1 if text.x == 0 else current_line
            if single_line and current_line > 0:
                return
            
            text_y = y + line_height + current_line * line_height
            canvas.draw_text(text.text, x + text.x, text_y )