from talon import Context, Module, actions, app, skia, cron, ctrl, scope, canvas, registry, settings, ui
from talon.types import Point2d
from abc import ABCMeta
import numpy
from user.talon_hud.base_widget import BaseWidget
from user.talon_hud.utils import layout_rich_text, HudRichTextLine

class LayoutWidget(BaseWidget):
    """This widget has a layout pass and changes the canvas size based on the content"""
    
    resize_canvas_stage = 2
    resize_stage_resize = 1
    resize_stage_listener = 0
    
    def refresh(self, new_content):
        self.resize_canvas_stage = 2
    
    def start_setup(self, setup_type):
        if setup_type in ["font_size", "position"] and self.setup_type != setup_type:
            # First resize the canvas back to the limit to make sure the content doesn't get clipped
            rect = ui.Rect(self.limit_x, self.limit_y, self.limit_width, self.limit_height)
            self.canvas.set_rect(rect)
        
        super().start_setup(setup_type)
            
    def setup_move(self, pos):
        self.resize_canvas_stage = 2
        super().setup_move(pos)
            
    def layout_content(self, canvas, paint):
        # Determine the dimensions and positions of the content
        return {"rect": ui.Rect(self.limit_x, self.limit_y, self.limit_width, self.limit_height)}
        
    def draw_content(self, canvas, paint, dimensions) -> bool:
        # Draw the content using the layout given dimensions
        return False
        
    def draw(self, canvas) -> bool:
        self.resize_canvas_stage = max(0, self.resize_canvas_stage - 1)
        
        # During any content or manual resizing, disable the mouse blocking behavior
        if self.setup_type != "" and self.resize_canvas_stage == self.resize_stage_resize and self.mouse_enabled == True:
            self.canvas.blocks_mouse = False
            self.canvas.unregister('mouse', self.on_mouse)
        
        paint = self.draw_setup_mode(canvas)
        
        content_dimensions = self.layout_content(canvas, paint)
        
        # Debug layout size / position
        #paint.color = "00FF00"
        #paint.style = paint.Style.STROKE
        #canvas.draw_rect(content_dimensions["rect"])        
        
        continue_drawing = self.draw_content(canvas, paint, content_dimensions)
        
        # Automatically resize the canvas based on the content to make sure no dead zones 
        # will show up when clicking in or near the text panel
        if self.setup_type == "":
            if self.resize_canvas_stage == self.resize_stage_resize:
                rect = content_dimensions["rect"]
                self.canvas.set_rect(rect)
            elif self.mouse_enabled == True and self.resize_canvas_stage == self.resize_stage_listener:
                self.canvas.blocks_mouse = True
                self.canvas.register('mouse', self.on_mouse)            

        return self.resize_canvas_stage > 0 or continue_drawing
        
    def draw_rich_text(self, canvas, paint, rich_text, x, y, line_height, single_line=False):
        # Draw text line by line
        text_colour = self.theme.get_colour('text_box_colour')
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