from talon import skia, ui, Module, cron, actions, clip
from talon.types import Point2d as Point2d
from user.talon_hud.base_widget import BaseWidget
from user.talon_hud.layout_widget import LayoutWidget
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import determine_screen_for_pos, layout_rich_text
from user.talon_hud.content_types import HudButton
import numpy

class HeadUpContextMenu(LayoutWidget):
    preferences = HeadUpDisplayUserWidgetPreferences(type="context_menu", x=50, y=100, width=200, height=200, limit_x=50, limit_y=100, limit_width=350, limit_height=400, enabled=True, alignment="left", expand_direction="down", font_size=18)
    mouse_enabled = True
    mark_position_invalid = False

    # Top, right, bottom, left, same order as CSS padding
    padding = [8, 8, 8, 8]
    line_padding = 8
    image_size = 20

    connected_widget = None
    button_hovered = -1
    default_buttons = [{
            'icon': None,
            'type': 'close',
            'text': 'Close panel',
            'rect': ui.Rect(0, 0, 0, 0)
        }, {
            'icon': None,        
            'type': 'cancel',
            'text': 'Cancel options',
            'rect': ui.Rect(0, 0, 0, 0)
        }]
    buttons = []

    subscribed_content = ["mode", "context_menu_buttons"]
    content = {
        'mode': 'command'
    }
    animation_max_duration = 0
        
    def on_mouse(self, event):
        pos = event.gpos
        
        button_hovered = -1
        for index, button in enumerate(self.buttons):
            br = button['rect']
            if pos.x >= br.x and pos.x <= br.x + br.width \
                and pos.y >= br.y and pos.y <= br.y + br.height:
                button_hovered = index

        if button_hovered != self.button_hovered:
            self.button_hovered = button_hovered
            self.canvas.resume()
            
        if event.event == "mouseup" and event.button == 0 and button_hovered != -1:
            clicked_button_type = self.buttons[button_hovered]['type']
            self.button_hovered = -1
            if clicked_button_type == "copy":
                if self.connected_widget:
                    self.connected_widget.copy_contents()
                actions.user.add_hud_log("event", "Copied contents to clipboard!")
            elif clicked_button_type == "close":
                if self.connected_widget:
                    self.connected_widget.disable(True)
            self.disconnect_widget()
            
    def connect_widget(self, widget: BaseWidget, pos_x: int, pos_y: int, buttons: list[HudButton]):        
        # Connect a widget up to context menu and move the context menu over
        self.limit_x = pos_x
        self.limit_y = pos_y
        self.x = pos_x
        self.y = pos_y
        self.connected_widget = widget
    
        if self.enabled == False:
            self.mark_position_invalid = True
            self.mark_layout_invalid = True            
            self.enable()
        else:
            self.mark_position_invalid = True
            self.mark_layout_invalid = True
            self.canvas.move(pos_x, pos_y)
            self.canvas.resume()
            
        self.buttons = list(self.default_buttons)
        if len(buttons) > 0:
            self.buttons[:0] = buttons
            
    def disconnect_widget(self):
        self.connected_widget = None
        self.disable(True)
            
    def draw(self, canvas) -> bool:
        if not self.mark_position_invalid:
            return super().draw(canvas)
        else:
            # Reposition the canvas to fit the contents in the screen
            screen = determine_screen_for_pos(Point2d(self.x, self.y))
            layout = self.layout_content(canvas, canvas.paint)
            dimensions = layout[self.page_index]['rect']
            
            should_go_left = dimensions.x + dimensions.width >= screen.x + screen.width
            should_go_up = dimensions.y + dimensions.height >= screen.y + screen.height
            can_go_middle_hor = dimensions.x + dimensions.width / 2 < screen.x + screen.width
            can_go_middle_ver = dimensions.y + dimensions.height / 2 < screen.y + screen.height            
            
            if can_go_middle_hor:
                self.limit_x = int(dimensions.x - dimensions.width / 2)
            elif should_go_left:
                self.limit_x = int(dimensions.x - dimensions.width)
            self.x = self.limit_x    

            if can_go_middle_ver:
                self.limit_y = int(dimensions.y - dimensions.height / 2 if not can_go_middle_hor else self.limit_y)
            if should_go_up:
                self.limit_y = int(dimensions.y - dimensions.height)
            self.y = self.limit_y
            
            if self.canvas:
                self.canvas.move(self.x, self.y)
                self.mouse_capture_canvas.set_rect(ui.Rect(self.x, self.y, dimensions.width, dimensions.height))
            self.mark_position_invalid = False
            return True
            
    def layout_content(self, canvas, paint):
        paint.textsize = self.font_size
        
        horizontal_alignment = "right" if self.limit_x < self.x else "left"
        vertical_alignment = "bottom" if self.limit_y < self.y else "top"
    
        total_width = 0
        button_layout = []
        total_text_width = 0
        total_button_height = 0
        for index, button in enumerate(self.buttons):
            icon_offset = 0
            if 'icon' in button and button['icon'] != None:
                icon_offset = self.image_size + self.padding[3] * 3
            button_rich_text = layout_rich_text(paint, button['text'], \
                self.limit_width - icon_offset - self.padding[3] * 2 - self.padding[1] * 2, self.limit_height)                
            
            line_count = 0
            button_text_height = 0
            for index, text in enumerate(button_rich_text):
                line_count = line_count + 1 if text.x == 0 else line_count
                current_line_length = current_line_length + text.width if text.x != 0 else text.width + icon_offset
                total_text_width = max( total_text_width, current_line_length )
                button_text_height = button_text_height + text.height + self.line_padding if text.x == 0 else button_text_height        
            total_button_height += button_text_height + self.padding[0] * 2
            
            button_layout.append({
                'button': button,
                'rich_text': button_rich_text,
                'line_count': line_count,
                'text_height': button_text_height
            })
    
        content_width = min(self.limit_width, max(self.width, total_text_width + self.padding[1] * 2 + self.padding[3] * 2))
        content_height = min(self.limit_height, max(self.height, total_button_height + self.padding[0] * 2 + self.padding[2] * 2))
    
        return [{
            "rect": ui.Rect(self.x, self.y, content_width, content_height),
            "button_layouts": button_layout
        }]
    
    def draw_content(self, canvas, paint, dimensions) -> bool:
        paint.textsize = self.font_size
        paint.style = paint.Style.FILL
        
        # Draw the background first
        background_colour = self.theme.get_colour('context_menu_background', 'F5F5F5')
        paint.color = background_colour
        self.draw_background(canvas, paint, dimensions["rect"])
        
        self.draw_content_buttons(canvas, paint, dimensions)
        
        return False
    
    def draw_content_buttons(self, canvas, paint, dimensions):
        """Draws the content buttons"""
        paint.textsize = self.font_size
        content_dimensions = dimensions["rect"]
       
        base_button_x = content_dimensions.x + self.padding[3]
        icon_button_x = base_button_x + self.image_size + self.padding[3]
        button_y = content_dimensions.y + self.padding[0]

        for index, button_layout in enumerate(dimensions['button_layouts']):
            paint.color = 'AAAAAA' if self.button_hovered == index else 'CCCCCC'
            button_height = self.padding[0] + button_layout['text_height'] + self.padding[2]
            rect = ui.Rect(base_button_x, button_y, content_dimensions.width - self.padding[3] - self.padding[1], button_height)
            self.buttons[index]['rect'] = rect
            canvas.draw_rrect( skia.RoundRect.from_rect(rect, x=10, y=10) )
            
            # Draw button icon on the left in the middle
            button_icon = button_layout['button']['icon'] if 'icon' in button_layout['button'] else None
            if button_icon:
                image = self.theme.get_image(button_icon)
                canvas.draw_image(image, base_button_x + self.padding[3], button_y + button_height / 2 - image.height / 2)
            
            paint.color = '000000'
            line_height = ( button_layout['text_height'] ) / button_layout['line_count']
            self.draw_rich_text(canvas, paint, button_layout['rich_text'], 
                base_button_x + self.padding[3] if not button_icon else icon_button_x + self.padding[3], 
                button_y + self.padding[0] / 2, line_height)
            button_y += button_height + self.padding[0]

    def draw_background(self, canvas, paint, rect):
        radius = 10
        rrect = skia.RoundRect.from_rect(rect, x=radius, y=radius)
        canvas.draw_rrect(rrect)
        paint.style = paint.Style.STROKE
        paint.color = '000000'
        canvas.draw_rrect(rrect)
        paint.style = paint.Style.FILL