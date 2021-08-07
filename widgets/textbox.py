from talon import skia, ui, Module, cron, actions, clip
from user.talon_hud.layout_widget import LayoutWidget
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import layout_rich_text, remove_tokens_from_rich_text, HudRichTextLine
from user.talon_hud.content_types import HudPanelContent
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
    }]
    
    # All the footer icons in a right to left order
    footer_icon_hovered = -1
    footer_icons = [{
        "type": "next", 
        "pos": [0,0]
    },{
        "type": "previous",
        "pos": [0,0]
    }]

    subscribed_content = ["mode"]
    content = {
        'mode': 'command',
    }
    panel_content = HudPanelContent('', '', [''], [], 0, False)    
    animation_max_duration = 60
        
    def copy_contents(self):
        clip.set_text(remove_tokens_from_rich_text(self.panel_content.content[0]))
    
    def on_mouse(self, event):
        pos = numpy.array(event.gpos)
        
        icon_hovered = -1
        for index, icon in enumerate(self.icons):
            if (numpy.linalg.norm(pos - numpy.array([icon['pos'][0], icon['pos'][1]])) < self.icon_radius):
                icon_hovered = index
                
        footer_icon_hovered = -1
        for index, icon in enumerate(self.footer_icons):
            if (numpy.linalg.norm(pos - numpy.array([icon['pos'][0], icon['pos'][1]])) < self.icon_radius):
                footer_icon_hovered = index

        if icon_hovered != self.icon_hovered or footer_icon_hovered != self.footer_icon_hovered:
            self.icon_hovered = icon_hovered
            self.footer_icon_hovered = footer_icon_hovered
            self.canvas.resume()
        
        if event.event == "mouseup" and event.button == 0:
            clicked_icon_type = None
            if icon_hovered != -1:
                clicked_icon_type = self.icons[icon_hovered]['type']
            elif footer_icon_hovered != -1:
                clicked_icon_type = self.footer_icons[footer_icon_hovered]['type']
                
            if clicked_icon_type == "close":
                self.disable(True)
            elif clicked_icon_type == "minimize":
                self.minimized = not self.minimized
                self.mark_layout_invalid = True
                self.canvas.resume()
            elif clicked_icon_type == "next":
                new_page_index = min(self.page_index + 1, len(self.layout) - 1)
                if new_page_index != self.page_index:                
                    self.page_index = new_page_index
                    self.canvas.resume()
            elif clicked_icon_type == "previous":
                new_page_index = max(self.page_index - 1, 0)
                if new_page_index != self.page_index:                
                    self.page_index = new_page_index
                    self.canvas.resume()
         

        if event.button == 1 and event.event == "mouseup":            
            actions.user.show_context_menu(self.id, event.gpos.x, event.gpos.y, [])

        if event.button == 0 and event.event == "mouseup":
            actions.user.hide_context_menu()

        # Allow dragging and dropping with the mouse
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
        header_title = self.panel_content.title if self.panel_content.title != "" else self.id
        header_text = layout_rich_text(paint, header_title, self.limit_width - icon_size, self.limit_height)
        content_text = [] if self.minimized else layout_rich_text(paint, self.panel_content.content[0], layout_width, self.limit_height)
        
        layout_pages = []
        
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
        
        page_height_limit = self.limit_height - header_height * 2
        
        # We do not render content if the text box is minimized
        current_content_height = 0
        current_page_text = []
        current_line_height = 0
        if not self.minimized:
            line_count = 0
            for index, text in enumerate(content_text):
                line_count = line_count + 1 if text.x == 0 else line_count
                current_line_length = current_line_length + text.width if text.x != 0 else text.width
                total_text_width = max( total_text_width, current_line_length )
                total_text_height = total_text_height + text.height + self.line_padding if text.x == 0 else total_text_height
                
                current_content_height = total_text_height + self.padding[0] + self.padding[2] + header_height
                current_line_height = text.height + self.line_padding
                if page_height_limit > current_content_height:
                    current_page_text.append(text)
                    
                # We have exceeded the page height limit, append the layout and try again
                else:
                    width = min( self.limit_width, max(self.width, total_text_width + self.padding[1] + self.padding[3]))
                    content_height = total_text_height - current_line_height
                    height = min(self.limit_height, max(self.height, content_height))
                    x = self.x if horizontal_alignment == "left" else self.limit_x + self.limit_width - width
                    y = self.limit_y if vertical_alignment == "top" else self.limit_y + self.limit_height - height
                    layout_pages.append({
                        "rect": ui.Rect(x, y, width, height), 
                        "line_count": max(1, line_count),
                        "header_text": header_text,
                        "icon_size": icon_size,
                        "content_text": current_page_text,
                        "header_height": header_height,
                        "content_height": current_content_height - current_line_height
                    })
                    
                    # Reset the variables
                    total_text_height = current_line_height
                    current_page_text = [text]
                    line_count = 1
                  
        # Make sure the remainder of the content gets placed on the final page
        if len(current_page_text) > 0 or len(layout_pages) == 0:
            
            # If we are dealing with a single line going over to the only other page
            # Just remove the footer to make up for space
            if len(layout_pages) == 1 and line_count == 1:
                layout_pages[0]['line_count'] = layout_pages[0]['line_count'] + 1
                layout_pages[0]['content_text'].extend(current_page_text)
                layout_pages[0]['content_height'] += current_line_height
            else: 
                width = min( self.limit_width, max(self.width, total_text_width + self.padding[1] + self.padding[3]))
                content_height = header_height if self.minimized else total_text_height + self.padding[0] + self.padding[2] + header_height
                height = header_height + self.padding[0] * 2 if self.minimized else min(self.limit_height, max(self.height, content_height))
                x = self.x if horizontal_alignment == "left" else self.limit_x + self.limit_width - width
                y = self.limit_y if vertical_alignment == "top" else self.limit_y + self.limit_height - height
                
                layout_pages.append({
                    "rect": ui.Rect(x, y, width, height), 
                    "line_count": max(1, line_count),
                    "header_text": header_text,
                    "icon_size": icon_size,
                    "content_text": current_page_text,
                    "header_height": header_height,
                    "content_height": content_height
                })        
        
        return layout_pages
    
    def draw_content(self, canvas, paint, dimensions) -> bool:
        paint.textsize = self.font_size
        
        paint.style = paint.Style.FILL
        
        # Draw the background first
        background_colour = self.theme.get_colour('text_box_background', 'F5F5F5')
        paint.color = background_colour
        self.draw_background(canvas, paint, dimensions["rect"])
        
        background_height = self.draw_content_text(canvas, paint, dimensions)
        self.draw_header(canvas, paint, dimensions)
        
        if not self.minimized and len(self.layout) > 1:
            self.draw_footer(canvas, paint, dimensions)
        
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
        
        x = dimensions.x + self.padding[3]
        canvas.draw_text(self.panel_content.title if self.panel_content.title else self.id, x, dimensions.y + self.font_size)
        
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

    def draw_footer(self, canvas, paint, dimensions):
        footer_height = dimensions["header_height"]
        dimensions = dimensions["rect"]

        # Small divider between the content and the header
        x = dimensions.x + self.padding[3]
        start_y = dimensions.y + dimensions.height - self.padding[0] - self.padding[2] / 2
        canvas.draw_text(str(self.page_index + 1 ) + ' of ' + str(len(self.layout)), x, start_y)
        canvas.draw_rect(ui.Rect(x - self.padding[3], start_y - footer_height, dimensions.width, 1))
        for index, icon in enumerate(self.footer_icons):
            icon_position = [x + dimensions.width - self.padding[3] - (self.icon_radius * 1.5 + ( index * self.icon_radius * 2.2 )),
                start_y - self.padding[0] * 2]
            self.footer_icons[index]['pos'] = icon_position
            paint.style = paint.Style.FILL
            
            hover_colour = '999999' if self.footer_icon_hovered == index else 'CCCCCC'            
            paint.shader = skia.Shader.linear_gradient(self.x, self.y, self.x, self.y + footer_height, ('AAAAAA', hover_colour), None)
            canvas.draw_circle(icon_position[0], icon_position[1], self.icon_radius, paint)
            image = self.theme.get_image(icon["type"] + "_icon")
            canvas.draw_image(image, icon_position[0] - image.width / 2, icon_position[1] - image.height / 2)
            


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