from talon import skia, ui, Module, cron, actions, clip
from user.talon_hud.layout_widget import LayoutWidget
from user.talon_hud.widgets.textpanel import HeadUpTextPanel
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import layout_rich_text, remove_tokens_from_rich_text, linear_gradient, hit_test_button
from user.talon_hud.content.typing import HudRichTextLine, HudPanelContent, HudButton, HudIcon, HudChoice
from talon.types.point import Point2d

class HeadUpChoicePanel(HeadUpTextPanel):
    preferences = HeadUpDisplayUserWidgetPreferences(type="choices", x=810, y=100, width=300, height=150, limit_x=810, limit_y=100, limit_width=300, limit_height=600, enabled=False, alignment="left", expand_direction="down", font_size=18)
    mouse_enabled = True

    # Top, right, bottom, left, same order as CSS padding
    padding = [3, 8, 8, 8]
    line_padding = 8
    
    # Options given to the context menu
    default_buttons = []
    buttons = []
    choices = []
    visible_indecis = []
    
    confirm_button = HudButton('check_icon', 'Confirm', ui.Rect(0, 0, 0, 0), print)
    confirm_hovered = False    
    choice_hovered = -1
    
    subscribed_content = ["mode"]
    content = {
        'mode': 'command',
    }
    animation_max_duration = 40
    image_size = 20
    
    def on_mouse(self, event):
        choice_hovered = -1
        pos = event.gpos
        for index, choice in enumerate(self.choices):
            if index in self.visible_indecis and hit_test_button(choice, pos):
                choice_hovered = index
        confirm_hovered = hit_test_button(self.confirm_button, pos)
        
        # Update the canvas if the hover state has changed
        if choice_hovered != self.choice_hovered or confirm_hovered != self.confirm_hovered:
            self.choice_hovered = choice_hovered
            if (self.choice_hovered != -1):
                self.icon_hovered = -1
                self.footer_icon_hovered = -1
                self.confirm_hovered = False
            elif confirm_hovered:
                self.choice_hovered = -1
                self.icon_hovered = -1
                self.footer_icon_hovered = -1
                self.confirm_hovered = confirm_hovered
            self.canvas.resume()
            
        if choice_hovered == -1 and confirm_hovered == False:
            super().on_mouse(event)
        elif event.event == "mouseup" and event.button == 0:
            if confirm_hovered:
                self.confirm_button.callback()
            else:
                self.select_choice(self.choice_hovered)
    
    def select_choice(self, choice_index):
        # Quick hack to add confirm button with an index above the choice length
        if choice_index > len(self.choices) - 1:
            self.confirm_button.callback()
        else:    
            self.choices[choice_index].selected = not self.choices[choice_index].selected
            if self.panel_content.choices and self.panel_content.choices.multiple:
                self.canvas.resume()
            else:
                for index, choice in enumerate(self.choices):
                    self.choices[index].selected = index == choice_index
                self.confirm_choices()
            
    
    def pick_choice(self, choices: list[HudChoice]):
        # Send a list of choices back in case of multiple choice, send back a single in case of single choice
        choices_data = list(map(lambda choice: choice.data, choices))
        keep_open = False
        if self.panel_content.choices and self.panel_content.choices.multiple:
            keep_open = self.panel_content.choices.callback(choices_data)
        else:
            keep_open = self.panel_content.choices.callback(choices_data[0] if len(choices_data) > 0 else None)
        
        if not keep_open:
            self.disable(True)
        
    def confirm_choices(self):
        choices = list(filter(lambda choice: choice.selected, self.choices))
        self.pick_choice(choices)        
    
    def update_panel(self, panel_content) -> bool:
        # Update the content buttons
        self.choices = list(panel_content.choices.choices) if panel_content.choices else []
        return super().update_panel(panel_content)

    def layout_content(self, canvas, paint):            
        confirm_button_height = 0
        
        # Calculate the height required for the confirm button
        text_box_header_height = self.padding[0] * 2 + self.icon_radius
        
        page_height_limit = self.limit_height - text_box_header_height / 2 
        if self.panel_content.choices and self.panel_content.choices.multiple:
            confirm_rich_text = layout_rich_text(paint, self.confirm_button.text, self.limit_width - self.image_size, self.limit_height)
            confirm_button_height = self.padding[0] + self.padding[2]
            confirm_line_count = 0
            total_text_width = 0
            for index, text in enumerate(confirm_rich_text):
                confirm_line_count = confirm_line_count + 1 if text.x == 0 else confirm_line_count
                current_line_length = current_line_length + text.width if text.x != 0 else text.width + self.image_size
                total_text_width = max( total_text_width, current_line_length )
                confirm_button_height = confirm_button_height + text.height + self.line_padding if text.x == 0 else confirm_button_height        
            page_height_limit -= confirm_button_height + self.padding[2]
    
    
        # Set the height limit to the limit without the confirmation button before calculating the text layout
        current_height_limit = self.limit_height
        self.limit_height = page_height_limit
        layout_pages = super().layout_content(canvas, paint)
        for index, page in enumerate(layout_pages):
            layout_pages[index]['choice_layouts'] = []
            
        
        # Start the layout process of the choice buttons        
        if self.panel_content.choices and self.minimized == False: 
            last_layout_page = layout_pages[len(layout_pages) - 1]
            y = self.limit_y + last_layout_page['header_height']
            content_start_height = last_layout_page['content_height'] + self.padding[2]
            total_text_width = 0
            if content_start_height < page_height_limit:
                y = last_layout_page['content_height']
                total_text_width = last_layout_page['rect'].width
                        
            # Append buttons to the last layout page until the height limit would be exceeded
            # Then create new layouts
            total_button_height = 0
            for choice_index, choice in enumerate(self.panel_content.choices.choices):
                icon_offset = self.image_size
                if choice.image != None:
                    icon_offset = self.image_size * 2 + self.padding[3] * 3
                choice_rich_text = layout_rich_text(paint, str(choice_index + 1) + ". " + choice.text, \
                    self.limit_width - icon_offset, self.limit_height)
                
                line_count = 0
                button_text_height = 0
                button_y = self.limit_y + total_button_height + content_start_height
                for index, text in enumerate(choice_rich_text):
                    line_count = line_count + 1 if text.x == 0 else line_count
                    current_line_length = current_line_length + text.width if text.x != 0 else text.width + icon_offset
                    total_text_width = max( total_text_width, current_line_length )
                    button_text_height = button_text_height + text.height + self.line_padding if text.x == 0 else button_text_height
                
                button_height = (button_text_height + self.padding[0] * 3)
                if content_start_height + total_button_height + text_box_header_height * 2 + button_height < page_height_limit:
                    total_button_height += button_text_height + self.padding[0] * 3
                    layout_pages[len(layout_pages) - 1]['choice_layouts'].append({
                        'choice_index': choice_index,
                        'choice_y': button_y,
                        'choice': choice,
                        'rich_text': choice_rich_text,
                        'line_count': line_count,
                        'text_height': button_text_height + self.padding[0]
                    })
                    layout_pages[len(layout_pages) - 1]['rect'].height = total_button_height + content_start_height + text_box_header_height * 2
                    total_button_height += self.padding[0] * 2
                    
                # Next page of buttons - Layout like the text box with extras
                else:
                    total_button_height = button_height
                    content_start_height = 0
                    button_y = self.limit_y + content_start_height + total_button_height
                    
                    horizontal_alignment = "right" if self.limit_x < self.x else "left"
                    vertical_alignment = "bottom" if self.limit_y < self.y else "top"
                    height = total_button_height * 2 + text_box_header_height * 2 + self.padding[0] * 2 + self.padding[2] * 2
                    x = self.x if horizontal_alignment == "left" else self.limit_x + self.limit_width - width
                    y = self.limit_y if vertical_alignment == "top" else self.limit_y + self.limit_height - height
                    
                    layout_pages.append({
                        "rect": ui.Rect(x, y, total_text_width, height + text_box_header_height),
                        "line_count": 1,
                        "header_text": self.panel_content.title if self.panel_content.title != "" else self.id,
                        "icon_size": len(self.icons) * 2 * self.icon_radius,
                        "content_text": '',
                        "header_height": text_box_header_height,
                        "content_height": 1,
                        "choice_layouts": [{
                            'choice_index': choice_index,
                            'choice_y': button_y,
                            'choice': choice,
                            'rich_text': choice_rich_text,
                            'line_count': line_count,
                            'text_height': button_text_height + self.padding[0]
                        }]
                    })
                    total_button_height += self.padding[0] * 2 + button_text_height + self.padding[2]
                    
            layout_pages[len(layout_pages) - 1]['rect'].height += self.padding[2]
        
        
        # Layout for multiple confirm button
        if len(layout_pages) == 1:
            layout_pages[self.page_index]['rect'].height -= text_box_header_height * 2
        
        if confirm_button_height > 0:
            self.confirm_button.callback = self.confirm_choices
            for page_index in range(len(layout_pages)):
                layout_pages[page_index]['confirm'] = {
                    'rich_text': confirm_rich_text,
                    'line_count': confirm_line_count,
                    'rect': ui.Rect(layout_pages[page_index]['rect'].x + self.padding[3] / 2, self.limit_y + layout_pages[page_index]['rect'].height + self.padding[2] + self.padding[0],
                    layout_pages[page_index]['rect'].width - self.padding[1] - self.padding[3], confirm_button_height) 
                }
                layout_pages[page_index]['rect'].height += confirm_button_height + self.padding[2]
            layout_pages[self.page_index]['rect'].height -= confirm_button_height + self.padding[2]
        else:
            self.confirm_button.callback = lambda x: None
            self.confirm_button.rect = ui.Rect(0, 0, 0, 0)
            
        
        self.limit_height = current_height_limit
        return layout_pages
            
    def draw_choices(self, canvas, paint, layout):
        """Draws the choice buttons"""
        paint.textsize = self.font_size
        content_dimensions = layout["rect"]
        self.visible_indecis = []
       
        base_button_x = content_dimensions.x + self.padding[3] / 2
        icon_button_x = base_button_x + self.image_size + self.padding[3] / 2

        for index, choice_layout in enumerate(layout['choice_layouts']):
            paint.color = self.theme.get_colour('button_hover_background', 'AAAAAA') if self.choice_hovered == choice_layout['choice_index'] \
                else self.theme.get_colour('button_background', 'CCCCCC')
                
            self.visible_indecis.append(choice_layout['choice_index'])
            button_height = self.padding[0] / 2 + choice_layout['text_height'] + self.padding[2] / 2 
            rect = ui.Rect(base_button_x, choice_layout['choice_y'], content_dimensions.width - (self.padding[3] + self.padding[1] ) / 2, button_height)
            self.choices[choice_layout['choice_index']].rect = rect
            canvas.draw_rrect( skia.RoundRect.from_rect(rect, x=10, y=10) )
            
            # Selected style applied
            if choice_layout['choice'].selected:
                selected_colour = self.theme.get_colour('success_colour', '00CC00')
                if len(selected_colour) == 6:
                    selected_colour = selected_colour + "33"
                paint.color = selected_colour
                canvas.draw_rrect( skia.RoundRect.from_rect(rect, x=10, y=10) )
                paint.color = "000000"
                image = self.theme.get_image("check_icon")
                canvas.draw_image(image, content_dimensions.x + content_dimensions.width - self.padding[1] - image.width, choice_layout['choice_y'] + button_height / 2 - image.height / 2)
                
            
            # Draw choice icon on the left in the middle
            choice_icon = choice_layout['choice'].image
            if choice_icon:
                image = self.theme.get_image(choice_icon)
                canvas.draw_image(image, content_dimensions.x + self.padding[3], choice_layout['choice_y'] + button_height / 2 - image.height / 2)
            
            paint.color = self.theme.get_colour('button_hover_text_colour', '000000') if self.choice_hovered == choice_layout['choice_index'] \
                else self.theme.get_colour('button_text_colour', '000000')
            line_height = ( choice_layout['text_height'] ) / choice_layout['line_count']
            self.draw_rich_text(canvas, paint, choice_layout['rich_text'], 
                base_button_x + self.padding[3] if not choice_icon else base_button_x + self.padding[3] + self.image_size, 
                choice_layout['choice_y'] - self.padding[0] / 2, line_height)

    def draw_content_text(self, canvas, paint, layout) -> int:
        """Draws the content and returns the height of the drawn content"""
        super().draw_content_text(canvas, paint, layout)
        if self.minimized:
            return        
        self.draw_choices(canvas, paint, layout)

        # Draw multiple choice confirm button
        if self.panel_content.choices and self.panel_content.choices.multiple:
            base_button_x = layout['rect'].x
            self.confirm_button.rect = ui.Rect(layout['confirm']['rect'].x, layout['confirm']['rect'].y, layout['confirm']['rect'].width, layout['confirm']['rect'].height )
            paint.color = self.theme.get_colour('button_hover_background', 'AAAAAA') if self.confirm_hovered else self.theme.get_colour('button_background', 'CCCCCC')
            button_rect = ui.Rect(base_button_x, self.confirm_button.rect.y, layout['rect'].width, self.confirm_button.rect.height)
            canvas.draw_rrect( skia.RoundRect.from_rect(button_rect, x=10, y=10) )
            
            confirm_icon = self.confirm_button.image
            if confirm_icon:
                image = self.theme.get_image(confirm_icon)
                canvas.draw_image(image, base_button_x + self.padding[3], self.confirm_button.rect.y + self.confirm_button.rect.height / 2 - image.height / 2)
            
            paint.color = self.theme.get_colour('button_hover_text_colour', '000000') if self.confirm_hovered else self.theme.get_colour('button_text_colour', '000000')
            line_height = ( self.confirm_button.rect.height - self.padding[0] - self.padding[2] ) / layout['confirm']['line_count']
            self.draw_rich_text(canvas, paint, layout['confirm']['rich_text'], 
                base_button_x + self.padding[3] * 2 if not confirm_icon else base_button_x + self.padding[3] * 2 + self.image_size, 
                self.confirm_button.rect.y + self.padding[0], line_height)

    def resize_mouse_canvas(self, content_dimensions):
        rect = content_dimensions["rect"]
        if self.confirm_button.rect.height > 0:
            rect = ui.Rect(rect.x, rect.y, rect.width, rect.height + self.confirm_button.rect.height + self.padding[0] + self.padding[2])
        
        self.capture_rect = rect
        self.mouse_capture_canvas.set_rect(rect)
        self.mouse_capture_canvas.freeze()
        self.mark_layout_invalid = False
