from talon import skia, ui, Module, cron, actions, clip
from user.talon_hud.layout_widget import LayoutWidget
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import layout_rich_text, remove_tokens_from_rich_text, linear_gradient, hit_test_icon
from user.talon_hud.content.typing import HudRichTextLine, HudPanelContent, HudButton, HudIcon
from talon.types.point import Point2d

icon_radius = 10
def close_widget(widget):
    widget.disable(True)
    
def minimize_toggle_widget(widget):
    widget.minimized = not widget.minimized
    widget.drag_positions = []
    widget.start_setup("")    
    if widget.minimized:
        widget.set_preference("minimized", 1)
    else:
        widget.set_preference("minimized", 0)
    widget.mark_layout_invalid = True
    widget.canvas.resume()

class HeadUpTextPanel(LayoutWidget):
    preferences = HeadUpDisplayUserWidgetPreferences(type="text_box", x=1680, y=50, width=200, height=200, limit_x=1580, limit_y=50, limit_width=300, limit_height=400, enabled=False, alignment="left", expand_direction="down", font_size=18)
    mouse_enabled = True

    # Top, right, bottom, left, same order as CSS padding
    padding = [3, 20, 10, 8]
    line_padding = 6
    
    # Options given to the context menu
    default_buttons = [
        HudButton("copy_icon", "Copy contents", ui.Rect(0,0,0,0), lambda widget: widget.copy_contents())
    ]
    buttons = []
    
    # All the header icons in a right to left order
    icon_radius = 10
    icon_hovered = -1
    icons = [HudIcon("close", "", Point2d(0,0), icon_radius, close_widget),
        HudIcon("minimize", "", Point2d(0,0), icon_radius, minimize_toggle_widget),
    ]
    
    # All the footer icons in a right to left order
    footer_icon_hovered = -1
    footer_icons = [HudIcon("next", "next_icon", Point2d(0,0), icon_radius, lambda widget: widget.set_page_index(widget.page_index + 1)),
        HudIcon("previous", "previous_icon", Point2d(0,0), icon_radius, lambda widget: widget.set_page_index(widget.page_index - 1))
    ]

    subscribed_content = ["mode"]
    content = {
        'mode': 'command',
    }
    panel_content = HudPanelContent('', '', [''], [], 0, False)    
    animation_max_duration = 60
        
    def copy_contents(self):
        clip.set_text(remove_tokens_from_rich_text(self.panel_content.content[0]))
        actions.user.hud_add_log("event", "Copied contents to clipboard!")
    
    def update_panel(self, panel_content) -> bool:
        # Update the content buttons
        self.buttons = list(panel_content.buttons)
        self.buttons.extend(self.default_buttons)
        return super().update_panel(panel_content)
    
    def set_preference(self, preference, value, persisted=False):
        self.mark_layout_invalid = True
        super().set_preference(preference, value, persisted)
        
    def load_theme_values(self):
        self.intro_animation_start_colour = self.theme.get_colour_as_ints('intro_animation_start_colour')
        self.intro_animation_end_colour = self.theme.get_colour_as_ints('intro_animation_end_colour')
        self.blink_difference = [
            self.intro_animation_end_colour[0] - self.intro_animation_start_colour[0],
            self.intro_animation_end_colour[1] - self.intro_animation_start_colour[1],
            self.intro_animation_end_colour[2] - self.intro_animation_start_colour[2]        
        ]
    
    def on_mouse(self, event):
        icon_hovered = -1
        for index, icon in enumerate(self.icons):
            if hit_test_icon(icon, event.gpos):
                icon_hovered = index
                
        footer_icon_hovered = -1
        if icon_hovered == -1:
            for index, icon in enumerate(self.footer_icons):
                if hit_test_icon(icon, event.gpos):
                    footer_icon_hovered = index

        if icon_hovered != self.icon_hovered or footer_icon_hovered != self.footer_icon_hovered:
            self.icon_hovered = icon_hovered
            self.footer_icon_hovered = footer_icon_hovered
            self.canvas.resume()
        
        if event.event == "mouseup" and event.button == 0:
            clicked_icon = None
            if icon_hovered != -1:
                clicked_icon = self.icons[icon_hovered]
            elif footer_icon_hovered != -1:
                clicked_icon = self.footer_icons[footer_icon_hovered]
                
            if clicked_icon != None:
                self.icon_hovered = -1
                self.footer_icon_hovered = -1
                clicked_icon.callback(self)

        if event.button == 1 and event.event == "mouseup":            
            actions.user.show_context_menu(self.id, event.gpos.x, event.gpos.y, self.buttons)

        if event.button == 0 and event.event == "mouseup":
            actions.user.hide_context_menu()

        # Allow dragging and dropping with the mouse
        if icon_hovered == -1 and footer_icon_hovered == -1:
            super().on_mouse(event)
        
    def layout_content(self, canvas, paint):
        paint.textsize = self.font_size
        
        # Line padding needs to accumulate to at least 1.5 times the font size
        # In order to make it readable according to WCAG specifications
        # https://www.w3.org/TR/WCAG21/#visual-presentation
        self.line_padding = int(self.font_size / 2) + 1 if self.font_size <= 17 else 5
        
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
        current_content_height = self.font_size + self.line_padding
        current_page_text = []
        current_line_height = 0
        if not self.minimized:
            line_count = 0
            for index, text in enumerate(content_text):
                line_count = line_count + 1 if text.x == 0 else line_count
                current_line_length = current_line_length + text.width if text.x != 0 else text.width
                total_text_width = max( total_text_width, current_line_length )
                total_text_height = total_text_height + current_line_height if text.x == 0 else total_text_height
                current_content_height = total_text_height + self.padding[0] + self.padding[2] + header_height
                
                # Recalculate current line height if we are starting a new line
                if text.x == 0:
                    current_line_height = max(text.height, self.font_size) + self.line_padding
                else:
                    current_line_height = max(current_line_height,  max(text.height, self.font_size) + self.line_padding)

                if page_height_limit > current_content_height:
                    current_page_text.append(text)
                    
                # We have exceeded the page height limit, append the layout and try again
                else:
                    width = min( self.limit_width, max(self.width, total_text_width + self.padding[1] + self.padding[3]))
                    height = self.limit_height
                    x = self.x if horizontal_alignment == "left" else self.limit_x + self.limit_width - width
                    y = self.limit_y if vertical_alignment == "top" else self.limit_y + self.limit_height - height
                    layout_pages.append({
                        "rect": ui.Rect(x, y, width, height), 
                        "line_count": max(1, line_count - 1),
                        "header_text": header_text,
                        "icon_size": icon_size,
                        "content_text": current_page_text,
                        "header_height": header_height,
                        "content_height": current_content_height
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
                content_height = header_height if self.minimized else total_text_height + self.padding[0] + self.padding[2] + header_height * 2
                height = header_height + self.padding[0] * 2 if self.minimized else min(self.limit_height, max(self.height, content_height))
                x = self.x if horizontal_alignment == "left" else self.limit_x + self.limit_width - width
                y = self.limit_y if vertical_alignment == "top" else self.limit_y + self.limit_height - height
                
                layout_pages.append({
                    "rect": ui.Rect(x, y, width, height), 
                    "line_count": max(1, line_count + 2 ),
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
        
        paint.color = self.theme.get_colour('text_colour')
        self.draw_content_text(canvas, paint, dimensions)
        self.draw_header(canvas, paint, dimensions)
        if not self.minimized and len(self.layout) > 1:
            self.draw_footer(canvas, paint, dimensions)
            self.draw_footer_buttons(canvas, paint, dimensions)        
        self.draw_header_buttons(canvas, paint, dimensions)
        
        return False

    def draw_animation(self, canvas, animation_tick):
        if self.enabled:
            paint = canvas.paint
            if self.mark_layout_invalid and animation_tick == self.animation_max_duration - 1:
                self.layout = self.layout_content(canvas, paint)
                if self.page_index > len(self.layout) - 1:
                    self.page_index = len(self.layout) -1
            
            dimensions = self.layout[self.page_index]['rect']
            
            # Determine colour of the animation
            animation_progress = ( animation_tick - self.animation_max_duration ) / self.animation_max_duration
            red = self.intro_animation_start_colour[0] - int( self.blink_difference[0] * animation_progress )
            green = self.intro_animation_start_colour[1] - int( self.blink_difference[1] * animation_progress )
            blue = self.intro_animation_start_colour[2] - int( self.blink_difference[2] * animation_progress )
            red_hex = '0' + format(red, 'x') if red <= 15 else format(red, 'x')
            green_hex = '0' + format(green, 'x') if green <= 15 else format(green, 'x')
            blue_hex = '0' + format(blue, 'x') if blue <= 15 else format(blue, 'x')
            paint.color = red_hex + green_hex + blue_hex
            
            if self.minimized:
                 self.draw_background(canvas, paint, dimensions)
            else:
                 header_height = self.layout[self.page_index]['header_height']
                 growth = (self.animation_max_duration - animation_tick ) / self.animation_max_duration
                 easeInOutQuint = 16 * growth ** 5 if growth < 0.5 else 1 - pow(-2 * growth + 2, 5) / 2
                 rect = ui.Rect(dimensions.x, dimensions.y, dimensions.width, max(header_height, dimensions.height * easeInOutQuint))
                 self.draw_background(canvas, paint, rect)
            
            if animation_tick == 1:
                return self.draw(canvas)
            return True
        else:
            return False
    
    def draw_header(self, canvas, paint, dimensions):
        header_height = dimensions["header_height"]
        dimensions = dimensions["rect"]
        
        paint.color = self.theme.get_colour('text_colour')
        paint.font.embolden = True
        
        x = dimensions.x + self.padding[3]
        canvas.draw_text(self.panel_content.title if self.panel_content.title else self.id, x, dimensions.y + self.font_size)
        
        # Small divider between the content and the header
        if not self.minimized:
            paint.color = self.theme.get_colour('text_box_line', '000000')
            canvas.draw_rect(ui.Rect(x - self.padding[3], dimensions.y + header_height + self.padding[0] * 2, dimensions.width, 1))

    def draw_header_buttons(self, canvas, paint, dimensions):
        header_height = dimensions["header_height"]    
        dimensions = dimensions["rect"]    
        # Header button tray 
        x = dimensions.x
        for index, icon in enumerate(self.icons):
            # Minimize / maximize icon
            icon_position = Point2d(x + dimensions.width - (self.icon_radius * 1.5 + ( index * self.icon_radius * 2.2 )),
                dimensions.y + self.icon_radius + self.padding[0] / 2)
            self.icons[index].pos = icon_position
            paint.style = paint.Style.FILL
            if icon.id == "minimize":
                hover_colour = self.theme.get_colour('button_hover_background', '999999') if self.icon_hovered == index \
                    else self.theme.get_colour('button_background', 'CCCCCC')
                paint.shader = linear_gradient(self.x, self.y, self.x, self.y + header_height, (hover_colour, hover_colour))
                canvas.draw_circle(icon_position.x, icon_position.y, self.icon_radius, paint)
                
                text_colour = self.theme.get_colour('icon_colour', '000000')
                paint.shader = linear_gradient(self.x, self.y, self.x, self.y + header_height, (text_colour, text_colour))
        
                if not self.minimized:
                    canvas.draw_rect(ui.Rect(icon_position.x - self.icon_radius / 2, icon_position.y - 1, self.icon_radius, 2))
                else:
                    paint.style = paint.Style.STROKE
                    canvas.draw_rect(ui.Rect( 1 + icon_position.x - self.icon_radius / 2, icon_position.y - self.icon_radius / 2, 
                        self.icon_radius - 2, self.icon_radius - 2))                
            elif icon.id == "close":
                close_colour = self.theme.get_colour('close_icon_hover_colour') if self.icon_hovered == index else self.theme.get_colour('close_icon_accent_colour')            
                paint.shader = linear_gradient(self.x, self.y, self.x, self.y + header_height, (self.theme.get_colour('close_icon_colour'), close_colour))
                canvas.draw_circle(icon_position.x, icon_position.y, self.icon_radius, paint)
    

    def draw_footer(self, canvas, paint, dimensions):
        footer_height = dimensions["header_height"]
        dimensions = dimensions["rect"]

        # Small divider between the content and the header
        x = dimensions.x + self.padding[3]
        start_y = dimensions.y + dimensions.height - self.padding[0] - self.padding[2] / 2
        
        paint.color = self.theme.get_colour('text_colour')
        canvas.draw_text(str(self.page_index + 1 ) + ' of ' + str(len(self.layout)), x, start_y)
        paint.color = self.theme.get_colour('text_box_line', '000000')        
        canvas.draw_rect(ui.Rect(x - self.padding[3], start_y - footer_height, dimensions.width, 1))

    def draw_footer_buttons(self, canvas, paint, dimensions):
        footer_height = dimensions["header_height"]
        dimensions = dimensions["rect"]

        # Small divider between the content and the footer
        x = dimensions.x + self.padding[3]
        start_y = dimensions.y + dimensions.height - self.padding[0] - self.padding[2] / 2        
        for index, icon in enumerate(self.footer_icons):
            icon_position = Point2d(x + dimensions.width - self.padding[3] - (self.icon_radius * 1.5 + ( index * self.icon_radius * 2.2 )),
                start_y - self.padding[0] * 2)
            self.footer_icons[index].pos = icon_position
            paint.style = paint.Style.FILL
            
            hover_colour = self.theme.get_colour('button_hover_background', '999999') if self.footer_icon_hovered == index \
                else self.theme.get_colour('button_background', 'CCCCCC')
            paint.shader = linear_gradient(self.x, self.y, self.x, self.y + footer_height, ('AAAAAA', hover_colour))
            canvas.draw_circle(icon_position.x, icon_position.y, self.icon_radius, paint)
            image = self.theme.get_image(icon.image)
            if image:
                canvas.draw_image(image, icon_position.x - image.width / 2, icon_position.y - image.height / 2)


    def draw_content_text(self, canvas, paint, dimensions):
        """Draws the content and returns the height of the drawn content"""
        paint.textsize = self.font_size
        
        header_height = dimensions["header_height"]
        rich_text = dimensions["content_text"]
        content_height = dimensions["content_height"]
        line_count = dimensions["line_count"]
        dimensions = dimensions["rect"]
       
        text_x = dimensions.x + self.padding[3]
        text_y = dimensions.y + header_height + self.padding[0] * 2
        
        #line_height = ( content_height - header_height - self.padding[0] - self.padding[2] ) / line_count
        self.draw_rich_text(canvas, paint, rich_text, text_x, text_y, self.line_padding)

    def draw_background(self, canvas, paint, rect):
        radius = 10
        rrect = skia.RoundRect.from_rect(rect, x=radius, y=radius)
        canvas.draw_rrect(rrect)