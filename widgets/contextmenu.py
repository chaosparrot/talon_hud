from talon import skia, ui, cron, clip, canvas
from talon.types import Point2d as Point2d
from ..base_widget import BaseWidget
from ..layout_widget import LayoutWidget
from ..widget_preferences import HeadUpDisplayUserWidgetPreferences
from ..utils import determine_screen_for_pos, layout_rich_text, hit_test_button
from ..content.typing import HudButton
import numpy

def close_widget(widget: BaseWidget):
    widget.disable(True)
    
def noop(widget: BaseWidget):
    pass

class HeadUpContextMenu(LayoutWidget):
    preferences = HeadUpDisplayUserWidgetPreferences(type="context_menu", x=50, y=100, width=200, height=50, limit_x=50, limit_y=100, limit_width=300, limit_height=500, enabled=False, alignment="left", expand_direction="down", font_size=18)
    mouse_enabled = True
    mark_position_invalid = False

    # Top, right, bottom, left, same order as CSS padding
    padding = [8, 8, 8, 8]
    line_padding = 8
    image_size = 30

    connected_widget = None
    button_hovered = -1
    default_buttons = [
        HudButton(None, "Close panel", ui.Rect(0, 0, 0, 0), close_widget),
        HudButton(None, "Dismiss options", ui.Rect(0, 0, 0, 0), noop)
    ]
    buttons = []

    subscribed_content = ["mode", "context_menu_buttons"]
    content = {
        "mode": "command"
    }
    panel_content = None
    animation_max_duration = 0
    current_focus = None
        
    def on_mouse(self, event):
        pos = event.gpos
        
        button_hovered = -1
        for index, button in enumerate(self.buttons):
            if hit_test_button(button, pos):
                button_hovered = index

        if button_hovered != self.button_hovered:
            self.button_hovered = button_hovered
            self.canvas.resume()
            
        if event.event == "mouseup" and event.button == 0 and button_hovered != -1:
            self.click_button(self.button_hovered)
    
    def click_button(self, button_index):
        if button_index > -1 and button_index < len(self.buttons):
            self.button_hovered = -1
            if self.connected_widget:
                self.buttons[button_index].callback(self.connected_widget)
                self.event_dispatch.hide_context_menu()
    
    def enable(self, persisted=False):
        if not self.enabled:
            # Copied over from layout widget enabled to make sure blocks_mouse setting isn"t changed        
            if self.mouse_enabled:
                # Keep this canvas using the default backend to make clicks happen properly                
                self.mouse_capture_canvas = canvas.Canvas(min(self.x, self.limit_x), min(self.y, self.limit_y), max(self.width, self.limit_width), max(self.height, self.limit_height))            
                self.mouse_capture_canvas.blocks_mouse = True
                self.mouse_capture_canvas.register("mouse", self.on_mouse)
                self.mouse_capture_canvas.freeze()
            
            self.enabled = True
            self.canvas = self.generate_canvas(min(self.x, self.limit_x), min(self.y, self.limit_y), max(self.width, self.limit_width), max(self.height, self.limit_height))
            self.canvas.register("draw", self.draw_cycle)
            self.animation_tick = self.animation_max_duration if self.show_animations else 0
            self.canvas.resume()
            if persisted:
                self.preferences.enabled = True
                self.preferences.mark_changed = True
                self.event_dispatch.request_persist_preferences()
            self.cleared = False
    
    def connect_widget(self, widget: BaseWidget, pos_x: int, pos_y: int, buttons: list[HudButton]):        
        # Connect a widget up to context menu and move the context menu over
        self.limit_x = pos_x
        self.limit_y = pos_y
        self.x = pos_x
        self.y = pos_y
        self.connected_widget = widget
    
        self.mark_position_invalid = True
        self.mark_layout_invalid = True
        if self.enabled:
            self.canvas.move(pos_x, pos_y)
            self.canvas.resume()
            
        self.buttons = list(self.default_buttons)
        if len(buttons) > 0:
            self.buttons[:0] = buttons
         
        if self.enabled == False:
            self.enable()

    def disconnect_widget(self):
        self.connected_widget = None
        self.disable()
        self.current_focus = None
            
    def draw(self, canvas) -> bool:
        if not self.mark_position_invalid:
            return super().draw(canvas)
        else:
            # Reposition the canvas to fit the contents in the screen
            screen = determine_screen_for_pos(Point2d(self.x, self.y))
            layout = self.layout_content(canvas, canvas.paint)
            dimensions = layout[self.page_index]["rect"]
            if dimensions is not None and screen is not None:
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
                    self.mouse_capture_canvas.rect = ui.Rect(self.x, self.y, dimensions.width, dimensions.height)
                self.mark_position_invalid = False
            return True
            
    def layout_content(self, canvas, paint):
        paint.textsize = self.font_size
        
        horizontal_alignment = "right" if self.limit_x < self.x else "left"
        vertical_alignment = "bottom" if self.limit_y < self.y else "top"
    
        total_width = 0
        button_layout = []
        total_text_width = 0
        total_button_height = self.padding[0] + self.padding[2]
        for index, button in enumerate(self.buttons):
            icon_offset = 0
            if button.image:
                icon_offset = self.image_size + self.padding[3] * 3
            button_rich_text = layout_rich_text(paint, button.text, \
                self.limit_width - icon_offset - self.padding[3] * 2 - self.padding[1] * 2, self.limit_height)                
            
            line_count = 0
            button_text_height = self.font_size
            for index, text in enumerate(button_rich_text):
                line_count = line_count + 1 if text.x == 0 else line_count
                current_line_length = current_line_length + text.width if text.x != 0 else text.width + icon_offset
                total_text_width = max( total_text_width, current_line_length )
                button_text_height = button_text_height + self.font_size + self.line_padding if text.x == 0 and index != 0 else button_text_height
            
            if button.image != None:
                total_button_height += max(self.image_size + self.padding[0] + self.padding[2], 
                    button_text_height + self.padding[0] + self.padding[2])
            else:
                total_button_height += button_text_height + self.padding[0] + self.padding[2]
            
            button_layout.append({
                "button": button,
                "rich_text": button_rich_text,
                "line_count": line_count,
                "text_height": button_text_height
            })
        
        # Add the padding between the buttons
        total_button_height += (len(button_layout) - 1 ) * self.padding[0]
        content_width = min(self.limit_width, max(self.width, total_text_width + self.padding[1] * 2 + self.padding[3] * 2))
        content_height = min(self.limit_height, max(self.height, total_button_height))
    
        return [{
            "rect": ui.Rect(self.x, self.y, content_width, content_height),
            "button_layouts": button_layout
        }]
    
    def draw_content(self, canvas, paint, dimensions) -> bool:
        paint.textsize = self.font_size
        paint.style = paint.Style.FILL
        
        # Draw the background first
        background_colour = self.theme.get_colour("context_menu_background", "F5F5F5")
        paint.color = background_colour
        self.draw_background(canvas, paint, dimensions["rect"])
        
        self.draw_content_buttons(canvas, paint, dimensions)
        
        return False
    
    def redraw_focus(self):
        if self.enabled and self.canvas:
            self.canvas.resume()        
    
    def draw_content_buttons(self, canvas, paint, dimensions):
        """Draws the content buttons"""
        paint.textsize = self.font_size
        content_dimensions = dimensions["rect"]
        focus_colour = self.theme.get_colour("focus_colour")
       
        base_button_x = content_dimensions.x + self.padding[3]
        icon_button_x = base_button_x + self.image_size + self.padding[3]
        button_y = content_dimensions.y + self.padding[0]

        for index, button_layout in enumerate(dimensions["button_layouts"]):
            paint.color = self.theme.get_colour("button_hover_background", "AAAAAA") if self.button_hovered == index \
                else self.theme.get_colour("button_background", "CCCCCC")
            paint.style = paint.Style.FILL
            button_height = self.padding[0] + button_layout["text_height"] + self.padding[2]
            
            button_icon = button_layout["button"].image
            if button_icon:
                button_height = max(self.image_size + self.padding[0] + self.padding[2], button_height)
            rect = ui.Rect(base_button_x, button_y, content_dimensions.width - self.padding[3] - self.padding[1], button_height)
            self.buttons[index].rect = rect
            canvas.draw_rrect( skia.RoundRect.from_rect(rect, x=10, y=10) )
            
            # Draw a focus ring around the button
            if self.current_focus and ( self.current_focus.equals(button_layout["button"].text) or \
                self.current_focus.equals("closewidget") and button_layout["button"].text == "Close panel"):
                paint.style = paint.Style.STROKE
                paint.stroke_width = 4
                paint.color = focus_colour
                canvas.draw_rrect( skia.RoundRect.from_rect(rect, x=10, y=10) )
                paint.style = paint.Style.FILL
            
            button_text_y = button_y + self.padding[0] / 2
            
            # Draw button icon on the left in the middle
            if button_icon:
                image = self.theme.get_image(button_icon)
                canvas.draw_image(image, base_button_x + self.padding[3], button_y + button_height / 2 - image.height / 2)
                if button_layout["text_height"] < self.image_size:
                    button_text_y += ( self.image_size - button_layout["text_height"] ) / 2
            
            paint.color = self.theme.get_colour("button_hover_text_colour", "000000") if self.button_hovered == index \
                else self.theme.get_colour("button_text_colour", "000000")
                
            self.draw_rich_text(canvas, paint, button_layout["rich_text"], 
                base_button_x + self.padding[3] if not button_icon else icon_button_x + self.padding[3] / 2, 
                button_text_y, self.line_padding)
            button_y += button_height + self.padding[0]

    def draw_background(self, canvas, paint, rect):
        focused = self.current_focus is not None and self.current_focus.equals("menu")
        radius = 10					
        rrect = skia.RoundRect.from_rect(rect, x=radius, y=radius)
        canvas.draw_rrect(rrect)
        paint.style = paint.Style.STROKE
        paint.color = self.theme.get_colour("focus_colour") if focused else self.theme.get_colour("context_menu_border", "000000")
        paint.stroke_width = 4 if focused else 1
        
        if focused:
            canvas.draw_rrect(skia.RoundRect.from_rect(ui.Rect(rect.x + 2, rect.y + 2, rect.width, rect.height), x=radius, y=radius))        
        else:
            canvas.draw_rrect(rrect)
        paint.style = paint.Style.FILL
