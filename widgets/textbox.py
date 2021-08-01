from talon import skia, ui, Module, cron, actions, clip
from user.talon_hud.layout_widget import LayoutWidget
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import layout_rich_text, remove_tokens_from_rich_text, HudRichTextLine
import numpy

class HeadUpTextBox(LayoutWidget):
    preferences = HeadUpDisplayUserWidgetPreferences(type="text_box", x=1630, y=100, width=200, height=200, limit_x=1530, limit_y=100, limit_width=350, limit_height=400, enabled=False, alignment="left", expand_direction="down", font_size=18)
    minimized = False
    mouse_enabled = True

    # Top, right, bottom, left, same order as CSS padding
    padding = [3, 20, 10, 8]     
    line_padding = 8
    
    # All the header icons in a right to left order
    icon_radius = 10
    icon_hovered = -1
    icons = [{
        "type": "close",
        "pos": [0,0]        
    },{
        "type": "minimize",
        "pos": [0,0]
    },{
        "type": "copy",
        "pos": [0,0]
    }]

    subscribed_content = ["mode", "text_state"]
    content = {
        'mode': 'command',
        'textbox_header': 'Debug panel',
        'text_state': " "
    }
    animation_max_duration = 60
    
    def enable(self, persisted=False):
        super().enable(persisted)
    
    def on_mouse(self, event):
        pos = numpy.array(event.gpos)
        
        icon_hovered = -1
        for index, icon in enumerate(self.icons):
            if (numpy.linalg.norm(pos - numpy.array([icon['pos'][0], icon['pos'][1]])) < self.icon_radius):
                icon_hovered = index

        if icon_hovered != self.icon_hovered:
            self.icon_hovered = icon_hovered
            self.canvas.resume()
        
        if event.event == "mouseup" and event.button == 0 and icon_hovered != -1:
            clicked_icon_type = self.icons[icon_hovered]['type']
            if clicked_icon_type == "close":
                self.disable(True)
            elif clicked_icon_type == "minimize":
                self.minimized = not self.minimized
                self.mark_layout_invalid = True
                self.canvas.resume()
            elif clicked_icon_type == "copy":
                clip.set_text(remove_tokens_from_rich_text(self.content["text_state"]))
                actions.user.add_hud_log("event", "Copied contents of panel to clipboard!")
               
        if icon_hovered == -1:
            super().on_mouse(event)
        
    def layout_content(self, canvas, paint):
        paint.textsize = self.font_size
        
        horizontal_alignment = "right" if self.limit_x < self.x else "left"
        vertical_alignment = "bottom" if self.limit_y < self.y else "top"
    
        layout_width = max(self.width - self.padding[1] - self.padding[3] * 2, 
            self.limit_width - self.padding[1] * 2 - self.padding[3] * 2)
        icon_size = len(self.icons) * 2 * self.icon_radius
    
        """Calculates the width and the height of the content"""
        header_text = layout_rich_text(paint, self.content['textbox_header'], self.limit_width - icon_size, self.limit_height)
        content_text = [] if self.minimized else layout_rich_text(paint, self.content['text_state'], layout_width, self.limit_height)
        
        line_count = 0
        total_text_width = 0
        total_text_height = 0
        current_line_length = 0
        header_height = 0
        
        # The header can only be one line long, so only take the first line
        for index, text in enumerate(header_text):
            line_count = line_count + 1 if text.x == 0 else line_count
            if line_count <= 1:
                header_height = text.height + self.padding[0] * 2
                current_line_length = current_line_length + text.width + self.icon_radius * 1.5
                total_text_width = max( total_text_width, current_line_length )
        header_height = max(header_height, self.padding[0] * 2 + self.icon_radius)
        
        # We do not render content if the text box is minimized
        if not self.minimized:
            line_count = 0        
            for index, text in enumerate(content_text):
                line_count = line_count + 1 if text.x == 0 else line_count
                current_line_length = current_line_length + text.width if text.x != 0 else text.width
                total_text_width = max( total_text_width, current_line_length )
                total_text_height = total_text_height + text.height + self.line_padding if text.x == 0 else total_text_height        
            
        width = min( self.limit_width, max(self.width, total_text_width + self.padding[1] + self.padding[3]))
        content_height = header_height if self.minimized else total_text_height + self.padding[0] + self.padding[2] + header_height
        height = header_height + self.padding[0] * 2 if self.minimized else min(self.limit_height, max(self.height, content_height))
        x = self.x if horizontal_alignment == "left" else self.limit_x + self.limit_width - width
        y = self.limit_y if vertical_alignment == "top" else self.limit_y + self.limit_height - height
        
        return {
            "rect": ui.Rect(x, y, width, height), 
            "line_count": max(1, line_count),
            "header_text": header_text,
            "icon_size": icon_size,
            "content_text": content_text,
            "header_height": header_height,
            "content_height": content_height
        }
    
    def draw_content(self, canvas, paint, dimensions) -> bool:
        paint.textsize = self.font_size
        
        paint.style = paint.Style.FILL
        
        # Draw the background first
        background_colour = self.theme.get_colour('text_box_background', 'F5F5F5')
        paint.color = background_colour
        self.draw_background(canvas, paint, dimensions["rect"])
        
        background_height = self.draw_content_text(canvas, paint, dimensions)
        self.draw_header(canvas, paint, dimensions)
        
        return False

    def draw_animation(self, canvas, animation_tick):
        if self.enabled:
            return True
        else:
            return self.draw(canvas)
    
    def draw_header(self, canvas, paint, dimensions):
        header_height = dimensions["header_height"]
        dimensions = dimensions["rect"]
        
        paint.color = self.theme.get_colour('text_colour')
        paint.font.embolden = True
        
        # TODO RICH TEXT HEADER?
        x = dimensions.x + self.padding[3]
        canvas.draw_text(self.content['textbox_header'], x, dimensions.y + self.font_size)
        
        # Small divider between the content and the header
        if not self.minimized:
            canvas.draw_rect(ui.Rect(x - self.padding[3], dimensions.y + header_height + self.padding[0] * 2, dimensions.width, 1))
        
        # Header button tray 
        x = dimensions.x
        for index, icon in enumerate(self.icons):
            # Minimize / maximize icon
            icon_position = [x + dimensions.width - (self.icon_radius * 1.5 + ( index * self.icon_radius * 2.2 )),
                dimensions.y + self.icon_radius + self.padding[0] / 2]
            self.icons[index]['pos'] = icon_position
            paint.style = paint.Style.FILL
            if (icon['type'] in ["minimize", "help", "copy"] and self.minimized == False ) or icon['type'] == "minimize":
                hover_colour = '999999' if self.icon_hovered == index else 'CCCCCC'            
                paint.shader = skia.Shader.linear_gradient(self.x, self.y, self.x, self.y + header_height, ('AAAAAA', hover_colour), None)
                canvas.draw_circle(icon_position[0], icon_position[1], self.icon_radius, paint)
                paint.shader = skia.Shader.linear_gradient(self.x, self.y, self.x, self.y + header_height, ('000000', '000000'), None)
        
                if icon['type'] == "minimize":
                    if not self.minimized:
                        canvas.draw_rect(ui.Rect(icon_position[0] - self.icon_radius / 2, icon_position[1] - 1, self.icon_radius, 2))
                    else:
                        paint.style = paint.Style.STROKE
                        canvas.draw_rect(ui.Rect( 1 + icon_position[0] - self.icon_radius / 2, icon_position[1] - self.icon_radius / 2, 
                            self.icon_radius - 2, self.icon_radius - 2))
                else:
                    image = self.theme.get_image(icon["type"] + "_icon")
                    canvas.draw_image(image, icon_position[0] - image.width / 2, icon_position[1] - image.height / 2)
                
            elif icon['type'] == "close":
                close_colour = self.theme.get_colour('close_icon_hover_colour') if self.icon_hovered == index else self.theme.get_colour('close_icon_accent_colour')            
                paint.shader = skia.Shader.linear_gradient(self.x, self.y, self.x, self.y + header_height, (self.theme.get_colour('close_icon_colour'), close_colour), None)
                canvas.draw_circle(icon_position[0], icon_position[1], self.icon_radius, paint)

    def draw_content_text(self, canvas, paint, dimensions) -> int:
        """Draws the content and returns the height of the drawn content"""
        paint.textsize = self.font_size
        
        header_height = dimensions["header_height"]
        rich_text = dimensions["content_text"]
        content_height = dimensions["content_height"]
        line_count = dimensions["line_count"]
        dimensions = dimensions["rect"]
       
        text_x = dimensions.x + self.padding[3]
        text_y = dimensions.y + header_height + self.padding[0] * 2
        
        line_height = ( content_height - header_height - self.padding[0] - self.padding[2] ) / line_count
        self.draw_rich_text(canvas, paint, rich_text, text_x, text_y, line_height)

    def draw_background(self, canvas, paint, rect):
        radius = 10
        rrect = skia.RoundRect.from_rect(rect, x=radius, y=radius)
        canvas.draw_rrect(rrect)