from talon import skia, ui, Module, cron, actions
from user.talon_hud.base_widget import BaseWidget
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import layout_rich_text, HudRichTextLine
import numpy

class HeadUpTextBox(BaseWidget):
    preferences = HeadUpDisplayUserWidgetPreferences(type="text_box", x=1480, y=100, width=350, height=400, limit_x=1480, limit_y=100, limit_width=350, limit_height=400, enabled=False, alignment="left", expand_direction="down", font_size=18)

    vertical_text_padding = 4
    text_padding = 8
    text_padding_right = 20
    
    close_button_radius = 10
    close_icon_position = [0,0]
    close_icon_hovered = False    

    subscribed_content = ["mode", "text_state"]
    content = {
        'mode': 'command',
        'textbox_header': 'Debug panel',
        'text_state': " "
    }
    animation_max_duration = 60
    
    # Content resize flags
    resize_canvas_stage = 2
    resize_stage_resize = 1 # Remove the listeners and resize the canvas
    resize_stage_listener = 0 # Append the mouse click listener again here
    
    def refresh(self, new_content):
        self.resize_canvas_stage = 2
    
    def on_mouse(self, event):
        pos = numpy.array(event.gpos)
        
        if (numpy.linalg.norm(pos - numpy.array([self.close_icon_position[0], self.close_icon_position[1]])) 
            < self.close_button_radius):
            if not self.close_icon_hovered:
                self.close_icon_hovered = True
                self.canvas.resume()
            if (event.event == "mouseup" and event.button == 0):
                self.disable(True)
        else: 
            if self.close_icon_hovered:
                self.close_icon_hovered = False
                self.canvas.resume()
    
    def draw(self, canvas) -> bool:
        self.resize_canvas_stage = max(0, self.resize_canvas_stage - 1)
        
        # During any content or manual resizing, disable the mouse blocking behavior
        if self.setup_type != "" and self.resize_canvas_stage == self.resize_stage_resize:
            self.canvas.blocks_mouse = False
            self.canvas.unregister('mouse', self.on_mouse)
    
        paint = self.draw_setup_mode(canvas)
        header_height = 30
        paint.textsize = self.font_size

        # Do a layout pass to determine the size of the content
        dimensions, header_text, content_text = self.layout_content(canvas, paint)
        background_height = self.draw_content(header_height, canvas, paint, dimensions, content_text)
        self.draw_header(header_height, canvas, paint, dimensions, header_text)
        
        # Automatically resize the canvas based on the content to make sure no dead zones 
        # will show up when clicking in or near the text panel
        if self.setup_type == "":
            if self.resize_canvas_stage == self.resize_stage_resize:
                x = self.x if self.alignment == "left" else self.limit_x + self.limit_width - dimensions.width - self.text_padding_right - self.text_padding
                rect = ui.Rect(x, self.y, dimensions.width + self.text_padding_right + self.text_padding, background_height)
                self.canvas.set_rect(rect)
            elif self.resize_canvas_stage == self.resize_stage_listener:
                self.canvas.blocks_mouse = True
                self.canvas.register('mouse', self.on_mouse)            

        return self.resize_canvas_stage > 0

    def draw_animation(self, canvas, animation_tick):
        if self.enabled:
            return True
        else:
            return self.draw(canvas)
    
    def layout_content(self, canvas, paint) -> (ui.Rect, list[HudRichTextLine], list[HudRichTextLine]):
        """Calculates the width and the height of the content"""
        header_text = layout_rich_text(paint, self.content['textbox_header'], self.limit_width - self.close_button_radius * 1.5, self.limit_height)
        content_text = layout_rich_text(paint, self.content['text_state'], self.limit_width - self.text_padding_right * 2, self.limit_height)

        total_text_width = 0
        total_text_height = 0
        current_line_length = self.close_button_radius * 4
        line_count = 0
        
        # The header can only be one line long, so only take the first line
        for index, text in enumerate(header_text):
            line_count = line_count + 1 if text.x == 0 else line_count
            if line_count <= 1:
                current_line_length = current_line_length + text.width
                total_text_width = max( total_text_width, current_line_length )
        
        line_count = 0
        for index, text in enumerate(content_text):
            line_count = line_count + 1 if text.x == 0 else line_count
            current_line_length = current_line_length + text.width if text.x != 0 else text.width
            total_text_width = max( total_text_width, current_line_length )
            total_text_height = total_text_height + text.height + self.vertical_text_padding if text.x == 0 else total_text_height

        return ui.Rect(0, max(1, line_count), total_text_width, total_text_height), header_text, content_text

    def draw_header(self, header_height, canvas, paint, dimensions, rich_text):
        paint.color = self.theme.get_colour('text_colour')
        paint.font.embolden = True
        
        # TODO RICH TEXT HEADER
        x = self.x + self.text_padding if self.alignment == "left" else self.limit_x + self.limit_width - dimensions.width - self.text_padding
        canvas.draw_text(self.content['textbox_header'], x, self.y + self.font_size)
        
        # Small divider between the content and the header
        canvas.draw_rect(ui.Rect(x - self.text_padding, self.y + self.font_size + self.text_padding, 
            dimensions.width + self.text_padding_right if self.alignment == "left" 
            else dimensions.width + self.text_padding_right - self.text_padding, 1))
        close_colour = self.theme.get_colour('close_icon_hover_colour') if self.close_icon_hovered else self.theme.get_colour('close_icon_accent_colour')
        paint.style = paint.Style.FILL
        paint.shader = skia.Shader.linear_gradient(self.x, self.y, self.x, self.y + header_height, (self.theme.get_colour('close_icon_colour'), close_colour), None)
        
        # Closing button
        x = self.x + self.text_padding if self.alignment == "left" else self.limit_x + self.limit_width - dimensions.width - self.close_button_radius * 1.5 - self.text_padding
        self.close_icon_position = [x + dimensions.width + self.text_padding_right - self.close_button_radius * 1.5,
            self.y + self.close_button_radius + self.vertical_text_padding / 2]
        canvas.draw_circle(self.close_icon_position[0], self.close_icon_position[1], self.close_button_radius, paint)

    def draw_content(self, header_height, canvas, paint, dimensions, rich_text) -> int:
        """Draws the content and returns the height of the drawn content"""
        paint.textsize = self.font_size

        background_colour = self.theme.get_colour('text_box_background', 'F5F5F5')
        paint.color = background_colour
        text_padding = self.text_padding
        
        current_y = self.y + header_height if self.expand_direction == "down" else self.y + self.height                        
        log_height = self.vertical_text_padding * (1 + dimensions.y) + dimensions.height
    
        if self.expand_direction == "down":
            offset = 0
            current_y = current_y + offset
        else:
            offset = log_height
            current_y = current_y - offset
        
        text_width = dimensions.width
        element_width = dimensions.width if self.alignment == "left" else dimensions.width - self.text_padding

        text_x = self.x + text_padding if self.alignment == "left" else self.limit_x + self.limit_width - text_padding - text_width
        element_x = text_x - text_padding
        
        self.draw_background(canvas, element_x, current_y - header_height, element_width + self.text_padding_right, log_height + header_height, paint)
        line_height = dimensions.height / dimensions.y
        self.draw_rich_text(canvas, paint, rich_text, text_x, current_y, line_height, self.vertical_text_padding)
        return log_height + header_height


    def draw_rich_text(self, canvas, paint, rich_text, x, y, line_height, padding, single_line=False):
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
            
            text_y = y + line_height + current_line * padding + current_line * line_height
            canvas.draw_text(text.text, x + text.x, text_y )


    def draw_background(self, canvas, origin_x, origin_y, width, height, paint):
        radius = 10
        rect = ui.Rect(origin_x, origin_y, width, height)
        rrect = skia.RoundRect.from_rect(rect, x=radius, y=radius)
        canvas.draw_rrect(rrect)