from talon import skia, ui, Module, cron, actions, clip
from user.talon_hud.layout_widget import LayoutWidget
from user.talon_hud.widgets.textbox import HeadUpTextBox
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import layout_rich_text, remove_tokens_from_rich_text, linear_gradient, hit_test_button
from user.talon_hud.content.typing import HudRichTextLine, HudPanelContent, HudButton, HudIcon, HudChoice
from talon.types.point import Point2d

icon_radius = 10
def close_widget(widget):
    widget.disable(True)
    
def minimize_toggle_widget(widget):
    widget.minimized = not widget.minimized
    if widget.minimized:
        widget.set_preference("minimized", 1)
    else:
        widget.set_preference("minimized", 0)
    widget.mark_layout_invalid = True
    widget.canvas.resume()

class HeadUpChoicePanel(HeadUpTextBox):
    preferences = HeadUpDisplayUserWidgetPreferences(type="choices", x=810, y=100, width=300, height=150, limit_x=810, limit_y=100, limit_width=300, limit_height=600, enabled=False, alignment="left", expand_direction="down", font_size=18)
    mouse_enabled = True

    # Top, right, bottom, left, same order as CSS padding
    padding = [3, 8, 8, 8]
    line_padding = 8
    
    # Options given to the context menu
    default_buttons = []
    buttons = []
    choices = []
    
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
            if hit_test_button(choice, pos):
                choice_hovered = index
        
        # Update the canvas if the hover state has changed
        if choice_hovered != self.choice_hovered:
            self.choice_hovered = choice_hovered
            if (self.choice_hovered != -1):
                self.icon_hovered = -1
                self.footer_icon_hovered = -1
            self.canvas.resume()

        if choice_hovered == -1:
            super().on_mouse(event)        
        elif event.event == "mouseup" and event.button == 0:
            self.pick_choice(self.choices[self.choice_hovered].data)

    def pick_choice(self, choices: list[HudChoice]):
        self.panel_content.choices.callback(choices)
        self.disable(True)
    
    def update_panel(self, panel_content) -> bool:
        # Update the content buttons
        self.choices = list(panel_content.choices.choices) if panel_content.choices else []
        return super().update_panel(panel_content)

    def layout_content(self, canvas, paint):
        layout_pages = super().layout_content(canvas, paint)
        for index, page in enumerate(layout_pages):
            layout_pages[index]['choice_layouts'] = []
        
        # Start the layout process of the choice buttons        
        if self.panel_content.choices: 
            last_layout_page = layout_pages[len(layout_pages) - 1]
            y = self.limit_y + last_layout_page['header_height']
            page_height_limit = self.limit_height - last_layout_page['header_height'] / 2
            total_button_height = last_layout_page['content_height'] + self.padding[2] 
            if total_button_height < page_height_limit:
                y = last_layout_page['content_height']
                total_text_width = last_layout_page['rect'].width
            
            # Append buttons to the last layout page until the height limit would be exceeded
            # Then create new layouts
            for choice_index, choice in enumerate(self.panel_content.choices.choices):
                icon_offset = 0
                if choice.image != None:
                    icon_offset = self.image_size + self.padding[3] * 3
                choice_rich_text = layout_rich_text(paint, str(choice_index + 1) + ". " + choice.text, \
                    self.limit_width - icon_offset - self.padding[3] * 2 - self.padding[1] * 2, self.limit_height)                
                
                line_count = 0
                button_text_height = 0
                button_y = self.limit_y + total_button_height
                for index, text in enumerate(choice_rich_text):
                    line_count = line_count + 1 if text.x == 0 else line_count
                    current_line_length = current_line_length + text.width if text.x != 0 else text.width + icon_offset
                    total_text_width = max( total_text_width, current_line_length )
                    button_text_height = button_text_height + text.height + self.line_padding if text.x == 0 else button_text_height        
                total_button_height += button_text_height + self.padding[0] * 2
                
                layout_pages[len(layout_pages) - 1]['choice_layouts'].append({
                    'choice_index': choice_index,
                    'choice_y': button_y,
                    'choice': choice,
                    'rich_text': choice_rich_text,
                    'line_count': line_count,
                    'text_height': button_text_height
                })
                layout_pages[len(layout_pages) - 1]['rect'].height = total_button_height
                total_button_height += self.padding[0] * 2
                
        layout_pages[len(layout_pages) - 1]['rect'].height += self.padding[2]
        
        return layout_pages
            
    def draw_choices(self, canvas, paint, layout):
        """Draws the choice buttons"""
        paint.textsize = self.font_size
        content_dimensions = layout["rect"]
       
        base_button_x = content_dimensions.x + self.padding[3] / 2
        icon_button_x = base_button_x + self.image_size + self.padding[3] / 2

        for index, choice_layout in enumerate(layout['choice_layouts']):
            paint.color = self.theme.get_colour('button_hover_background', 'AAAAAA') if self.choice_hovered == choice_layout['choice_index'] \
                else self.theme.get_colour('button_background', 'CCCCCC')
            button_height = self.padding[0] / 2 + choice_layout['text_height'] + self.padding[2] / 2 
            rect = ui.Rect(base_button_x, choice_layout['choice_y'], content_dimensions.width - (self.padding[3] + self.padding[1] ) / 2, button_height)
            self.choices[index].rect = rect
            canvas.draw_rrect( skia.RoundRect.from_rect(rect, x=10, y=10) )
            
            # Draw choice icon on the left in the middle
            choice_icon = choice_layout['choice'].image
            if choice_icon:
                image = self.theme.get_image(choice_icon)
                canvas.draw_image(image, base_button_x + self.padding[3] / 2, choice_layout['choice_y'] + button_height / 2 - image.height / 2)
            
            paint.color = self.theme.get_colour('button_hover_text_colour', '000000') if self.choice_hovered == choice_layout['choice_index'] \
                else self.theme.get_colour('button_text_colour', '000000')
            line_height = ( choice_layout['text_height'] ) / choice_layout['line_count']
            self.draw_rich_text(canvas, paint, choice_layout['rich_text'], 
                base_button_x + self.padding[3] if not choice_icon else icon_button_x + self.padding[3] / 2, 
                choice_layout['choice_y'] + self.padding[0] / 2, line_height)


    def draw_content_text(self, canvas, paint, layout) -> int:
        """Draws the content and returns the height of the drawn content"""
        super().draw_content_text(canvas, paint, layout)
        self.draw_choices(canvas, paint, layout)