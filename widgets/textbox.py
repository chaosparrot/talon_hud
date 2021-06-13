from talon import skia, ui, Module, cron, actions
from user.talon_hud.base_widget import BaseWidget
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import layout_rich_text

text_state = """ a"""

class HeadUpTextBox(BaseWidget):
    preferences = HeadUpDisplayUserWidgetPreferences(type="text_box", x=1480, y=100, width=350, height=400, limit_x=1480, limit_y=100, limit_width=350, limit_height=400, enabled=False, alignment="left", expand_direction="down", font_size=18)

    subscribed_content = ["mode", "text_state"]
    content = {
        'mode': 'command',
        'textbox_header': 'This is a textbox header!',
        'text_state': text_state
    }
    
    animation_max_duration = 60
    
    def draw(self, canvas) -> bool:
        paint = self.draw_setup_mode(canvas)
            
        paint.textsize = self.font_size
        continue_drawing = False

        background_colour = self.theme.get_colour('text_box_background', 'F5F5F5')
        log_margin = 10
        text_padding = 8
        text_padding_right = 20
        vertical_text_padding = 4
        log_height = 30
        paint.color = background_colour
        
        current_y = self.y if self.expand_direction == "down" else self.y + self.height
                        
        rich_text = layout_rich_text(paint, self.content['text_state'], self.limit_width - 20, self.limit_height)
        total_text_width = 0
        total_text_height = 0
        current_line_length = 0
        line_count = 0
        for index, text in enumerate(rich_text):
            line_count = line_count + 1 if text.x == 0 else line_count
            current_line_length = current_line_length + text.width if text.x != 0 else text.width
            total_text_width = max( total_text_width, current_line_length )
            total_text_height = total_text_height + text.height + vertical_text_padding if text.x == 0 else total_text_height
        log_height = vertical_text_padding * (1 + line_count) + total_text_height
    
        if self.expand_direction == "down":
            offset = 0
            current_y = current_y + offset
        else:
            offset = log_height
            current_y = current_y - offset
        
        text_width = total_text_width
        element_width = text_padding + text_padding_right + text_width

        text_x = self.x + text_padding if self.alignment == "left" else self.x + self.width - text_padding - text_width
        element_x = text_x - text_padding
        
        self.draw_background(canvas, element_x, current_y, element_width, log_height, paint)
        
        # Draw text line by line
        text_colour = self.theme.get_colour('event_log_text_colour', self.theme.get_colour('text_colour'))
        error_colour = self.theme.get_colour('error_colour', 'AA0000')
        warning_colour = self.theme.get_colour('warning_colour', 'F75B00')
        success_colour = self.theme.get_colour('success_colour', '00CC00')
        info_colour = self.theme.get_colour('error_colour', '30AD9E')
        
        line_height = total_text_height / line_count
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
            text_y = current_y + line_height + current_line * vertical_text_padding + current_line * line_height
        
            canvas.draw_text(text.text, text_x + text.x, text_y )
            
        return continue_drawing
        
    def draw_animation(self, canvas, animation_tick):
        if self.enabled:
            return True
        else:
            return self.draw(canvas)

    def draw_background(self, canvas, origin_x, origin_y, width, height, paint):
        radius = 10
        rect = ui.Rect(origin_x, origin_y, width, height)
        rrect = skia.RoundRect.from_rect(rect, x=radius, y=radius)
        canvas.draw_rrect(rrect)