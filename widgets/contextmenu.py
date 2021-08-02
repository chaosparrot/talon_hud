from talon import skia, ui, Module, cron, actions, clip
from talon.types import Point2d as Point2d
from user.talon_hud.base_widget import BaseWidget
from user.talon_hud.layout_widget import LayoutWidget
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
import numpy

class HeadUpContextMenu(LayoutWidget):
    preferences = HeadUpDisplayUserWidgetPreferences(type="context_menu", x=50, y=100, width=200, height=200, limit_x=50, limit_y=100, limit_width=350, limit_height=400, enabled=True, alignment="left", expand_direction="down", font_size=18)
    mouse_enabled = True

    # Top, right, bottom, left, same order as CSS padding
    padding = [8, 8, 8, 8]     
    line_padding = 8

    connected_widget = None
    button_hovered = -1
    buttons = [{
            'type': 'copy',
            'text': 'Copy contents',
            'rect': ui.Rect(0, 0, 0, 0)
        }, {
            'type': 'close',
            'text': 'Close panel',
            'rect': ui.Rect(0, 0, 0, 0)
        }, {
            'type': 'cancel',
            'text': 'Cancel',
            'rect': ui.Rect(0, 0, 0, 0)
        }]

    subscribed_content = ["mode", "context_menu_buttons"]
    content = {
        'mode': 'command',
        'context_menu_buttons': [{
            'type': 'copy',
            'text': 'Copy contents'
        }, {
            'type': 'close',
            'text': 'Close panel'
        }, {
            'type': 'cancel',
            'text': 'Cancel'
        }]
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
            
    def connect_widget(self, widget: BaseWidget, pos_x: int, pos_y: int, buttons):
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
            
    def disconnect_widget(self):
        self.connected_widget = None
        self.disable(True)
            
    def layout_content(self, canvas, paint):
        paint.textsize = self.font_size
        
        horizontal_alignment = "right" if self.limit_x < self.x else "left"
        vertical_alignment = "bottom" if self.limit_y < self.y else "top"
    
        layout_width = max(self.width - self.padding[1] - self.padding[3] * 2, 
            self.limit_width - self.padding[1] * 2 - self.padding[3] * 2)
    
        return {
            "rect": ui.Rect(self.x, self.y, layout_width, self.height)
        }
    
    def draw_content(self, canvas, paint, dimensions) -> bool:
        paint.textsize = self.font_size
        paint.style = paint.Style.FILL
        
        # Draw the background first
        background_colour = self.theme.get_colour('context_menu_background', 'F5F5F5')
        paint.color = background_colour
        self.draw_background(canvas, paint, dimensions["rect"])
        
        # TODO BUTTON DRAWING
        paint.color = 'FF0000'
        #arrow_path = (float(self.x) + 50, float(self.y) + 50, float(self.x) + 100, float(self.y) + 100)
        #canvas.draw_path(arrow_path, paint)
        # TODO DIRECTION DRAWING
        background_height = self.draw_content_buttons(canvas, paint, dimensions)
        
        return False
    
    def draw_content_buttons(self, canvas, paint, dimensions) -> int:
        """Draws the content and returns the height of the drawn content"""
        paint.textsize = self.font_size        
        dimensions = dimensions["rect"]
       
        button_x = dimensions.x + self.padding[3]
        button_y = dimensions.y + self.padding[0]

        for index, button in enumerate(self.buttons):
            paint.color = 'AAAAAA' if self.button_hovered == index else 'CCCCCC'
            button_height = self.padding[0] + self.font_size + self.padding[2]
            rect = ui.Rect(button_x, button_y, dimensions.width - self.padding[3] - self.padding[1], button_height)
            self.buttons[index]['rect'] = rect
            canvas.draw_rrect( skia.RoundRect.from_rect(rect, x=10, y=10) )
            
            paint.color = '000000'
            canvas.draw_text(button['text'], button_x + self.padding[3], button_y + self.padding[0] / 2 + self.font_size)
            button_y += button_height + self.padding[0]

    def draw_background(self, canvas, paint, rect):
        radius = 10
        rrect = skia.RoundRect.from_rect(rect, x=radius, y=radius)
        canvas.draw_rrect(rrect)
        paint.style = paint.Style.STROKE
        paint.color = '000000'
        canvas.draw_rrect(rrect)
        paint.style = paint.Style.FILL
