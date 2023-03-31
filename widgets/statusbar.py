from ..base_widget import BaseWidget
from ..utils import linear_gradient
from ..widget_preferences import HeadUpDisplayUserWidgetPreferences
from ..content.typing import HudButton, HudStatusOption, HudStatusIcon
from talon import skia, ui, Module, cron, actions
import time
import numpy

# TODO FIX ISSUE WHERE ENABLING THE STATUS BAR WILL NOT RECOVER THE PROPER SUBSCRIPTIONS?
class HeadUpStatusBar(BaseWidget):

    allowed_setup_options = ["position", "dimension", "font_size"]
    mouse_enabled = True

    # Defaults defined using a 1920x1080 screen
    # Where the status bar sits just above the time in Windows
    preferences = HeadUpDisplayUserWidgetPreferences(type="status_bar", x=1630, y=930, width=250, height=50, enabled=True, sleep_enabled=True)

    # Difference array for colour transitions in animations
    blink_state = 0    
    blink_difference = [0, 0, 0]
    blink_colour = [0, 0, 0]
    icon_hover_index = -1
    icon_hover_activate_dwell_seconds = 1.5
    icon_positions = []
    icons = []

    # New content topic types
    topic_types = ["status_icons", "status_options"]
    current_topics = []
    subscriptions = ["*"]
    
    animation_max_duration = 60
    
    def refresh(self, new_content):
        if self.animation_tick == 0 and "event" in new_content and new_content["event"].topic_type == "variable" and new_content["event"].topic == "mode":
            if new_content["event"].content == "command":
                self.blink_colour = self.command_blink_colour
            elif new_content["event"].content == "dictation":
                self.blink_colour = self.dictation_blink_colour
            elif new_content["event"].content == "sleep":
                self.blink_colour = self.sleep_blink_colour
            
            # Calculate the colour difference between the blink and the next state
            # To make it easier to calculate during draw
            self.blink_difference = [
                self.background_colour[0] - self.blink_colour[0],
                self.background_colour[1] - self.blink_colour[1],
                self.background_colour[2] - self.blink_colour[2]
            ]
        
            self.blink_state = 100 if self.show_animations else 0
            
        self.update_icons()
        self.update_buttons()
        self.refresh_drawing(True)
    
    def update_buttons(self):
        buttons = []
        buttons.append(HudButton("", "Content toolkit", ui.Rect(0,0,0,0), lambda widget: actions.user.hud_toolkit_options()))
        status_options = self.content.get_topic("status_options")
        for status_option in status_options:
            if status_option.icon_topic in self.current_topics:
                if status_option.activated_option:
                    buttons.append( status_option.activated_option )
            else:
                if status_option.default_option:
                    buttons.append( status_option.default_option )
        
        self.buttons = buttons
    
    def update_icons(self):        
        self.icons = self.content.get_topic("status_icons")
        
    def on_mouse(self, event):
        pos = numpy.array(event.gpos)
        
        # Hit detection of buttons        
        hover_index = -1
        for index, icon in enumerate(self.icon_positions):
            if icon["icon"].callback and (numpy.linalg.norm(pos - numpy.array([icon["center_x"], icon["center_y"]])) < icon["radius"]):
                hover_index = index
                break
        
        if (event.event == "mousemove"):
            # Only resume for a frame if our button state has changed
            if (self.icon_hover_index != hover_index):
                self.icon_hover_index = hover_index                
                self.refresh_drawing()
        # Click a button instantly
        elif (event.event == "mouseup" and event.button == 0):
            self.icon_hover_index = hover_index
            self.activate_icon()
        
        # Right click menu
        elif (event.event == "mouseup" and event.button == 1):
            self.event_dispatch.show_context_menu(self.id, event.gpos, self.buttons)
        
        # Mouse dragging
        if hover_index == -1:
            super().on_mouse(event)
            
    def activate_icon(self):    
        if self.icon_hover_index < len(self.icon_positions) and self.icon_hover_index > -1:
            icon = self.icon_positions[self.icon_hover_index]["icon"]
            icon.callback(self, icon)
        self.icon_hover_index = -1
                
    def enable(self, persist=False):
        if not self.enabled:
            self.reset_blink()
            self.update_icons()
            self.update_buttons()
            super().enable(persist)
    
    def load_theme_values(self):
        self.command_blink_colour = self.theme.get_colour_as_ints("command_blink_colour")
        self.sleep_blink_colour = self.theme.get_colour_as_ints("sleep_blink_colour")
        self.dictation_blink_colour = self.theme.get_colour_as_ints("dictation_blink_colour")
        self.background_colour = self.theme.get_colour_as_ints("background_colour")
        self.intro_animation_start_colour = self.theme.get_colour_as_ints("intro_animation_start_colour")
        self.intro_animation_end_colour = self.theme.get_colour_as_ints("intro_animation_end_colour")
        self.reset_blink()
    
    def draw(self, canvas) -> bool:
        paint = self.draw_setup_mode(canvas)
        self.icon_positions = []
        stroke_width = 1.5
        focus_colour = self.theme.get_colour("focus_colour")
        focus_width = 4
        circle_margin = 4
        element_height = self.height - ( stroke_width * 2 )
        icon_diameter = self.height - ( circle_margin * 2 )
        element_width = self.width 
        
        # Draw the background with bigger stroke than 1px
        stroke_colours = (self.theme.get_colour("top_stroke_colour"), self.theme.get_colour("down_stroke_colour"))
        paint.shader = linear_gradient(self.x, self.y, self.x, self.y + element_height * 2, stroke_colours)
        self.draw_background(canvas, self.x, self.y, element_width, element_height + (stroke_width * 2), paint)
        focus_shader = linear_gradient(self.x, self.y, self.x, self.y + element_height * 2, (focus_colour, focus_colour))
            
        # Calculate the blinking colour
        continue_drawing = False
        if ( self.blink_state > 0 ):
            self.blink_state = max(0, self.blink_state - 4)        
            continue_drawing = self.blink_state > 0
            red = self.blink_colour[0] - int( self.blink_difference[0] * ( self.blink_state - 100 ) / 100 )
            green = self.blink_colour[1] - int( self.blink_difference[1] * ( self.blink_state - 100 ) / 100 )
            blue = self.blink_colour[2] - int( self.blink_difference[2] * ( self.blink_state - 100 ) / 100 )
        else:
            red, green, blue = self.background_colour            
        red_hex = "0" + format(red, "x") if red <= 15 else format(red, "x")
        green_hex = "0" + format(green, "x") if green <= 15 else format(green, "x")
        blue_hex = "0" + format(blue, "x") if blue <= 15 else format(blue, "x")
        
        mode = self.content.get_variable("mode", "command")
        
        # Draw the background based on the state
        accent_colour = red_hex + green_hex + blue_hex
        mode_colour = self.theme.get_colour( mode + "_mode_colour")
        background_shader = linear_gradient(self.x, self.y, self.x, self.y + element_height * 2, (mode_colour, accent_colour))
        paint.shader = background_shader
        self.draw_background(canvas, self.x + stroke_width, self.y + stroke_width, element_width - stroke_width * 2, element_height, paint)

        if self.focused and ( self.current_focus is None or self.current_focus.role == "widget" ):
            paint.style = canvas.paint.Style.STROKE
            paint.stroke_width = focus_width
            paint.shader = linear_gradient(self.x, self.y, self.x, self.y + element_height * 2, (focus_colour, focus_colour))
            self.draw_background(canvas, self.x + focus_width / 2, self.y + focus_width / 2, element_width - focus_width, element_height, paint)
            paint.style = canvas.paint.Style.FILL

        icon_texts = []

        # Draw icons
        icon_offset = 0
        hover_index = 0
        for index, icon in enumerate(self.icons):
            if icon.image is None or self.theme.get_image(icon.image) is None:
                if icon.text is not None:
                    icon_texts.append(icon.text)
                continue

            if self.focused and self.current_focus is not None and self.current_focus.role == "button" and self.current_focus.equals(icon.topic):
                paint.shader = focus_shader
                paint.style = paint.Style.STROKE
                paint.stroke_width = focus_width                
            elif (not icon.callback or (mode == "sleep" and self.icon_hover_index != hover_index)):
                paint.shader = background_shader
            else:
                button_colour = self.theme.get_colour("button_hover_colour") if self.icon_hover_index == hover_index else self.theme.get_colour("button_colour")                
                paint.shader = linear_gradient(self.x, self.y, self.x, self.y + element_height, (self.theme.get_colour("button_colour"), button_colour))
            
            self.draw_icon(canvas, self.x + stroke_width + circle_margin + icon_offset, self.y + circle_margin, icon_diameter, paint, icon)
            paint.style = paint.Style.FILL
            icon_offset += icon_diameter + circle_margin
            hover_index += 1

        height_center = self.y + element_height + ( circle_margin / 2 ) - ( element_height / 2 )

        # Draw selected programming language
        text_value = " ".join(icon_texts)
        if len(text_value) > 0:
            text_colour = self.theme.get_colour("text_colour")
            paint.shader = linear_gradient(self.x, self.y, self.x, self.y + element_height, (text_colour, text_colour))
            paint.style = paint.Style.STROKE
            paint.textsize = self.font_size
            text_x = self.x + stroke_width + circle_margin + icon_offset
            canvas.draw_text(text_value, text_x , height_center - circle_margin + paint.textsize / 2)
            paint.style = paint.Style.FILL
            canvas.draw_text(text_value, text_x, height_center - circle_margin + paint.textsize / 2)

        # Draw closing icon
        if not self.minimized:
            paint.style = paint.Style.FILL
            close_colour = self.theme.get_colour("close_icon_hover_colour") if self.icon_hover_index == len(self.icons) else self.theme.get_colour("close_icon_accent_colour")
            paint.shader = linear_gradient(self.x, self.y, self.x, self.y + element_height, (self.theme.get_colour("close_icon_colour"), close_colour))
            close_icon_diameter = icon_diameter / 2
            close_status_icon = HudStatusIcon("close", None, None, "Close Head up display", lambda widget, icon: actions.user.hud_disable())
            self.draw_icon(canvas, self.x + element_width - close_icon_diameter - close_icon_diameter / 2 - stroke_width, height_center - close_icon_diameter / 2, close_icon_diameter, paint, close_status_icon)

        # Reset the blink colour when the blink is finished
        if not continue_drawing:
            self.reset_blink()

        return continue_drawing
                
    def draw_animation(self, canvas, animation_tick) -> bool:
        paint = canvas.paint
        stroke_width = 1.5      
        end_element_width = self.width
        end_element_height = self.height
    
        element_height = 5 if animation_tick > 30 else min( end_element_height, max( 5, ( end_element_height / animation_tick * 7 ) ) )
        element_width = self.width if animation_tick < 40 else max( 10, ( self.width - element_height ) / (animation_tick - 39) )
        
        # Change the colour of the animation based on the current animation frame
        red = self.intro_animation_start_colour[0] - int( self.blink_difference[0] * ( animation_tick - self.animation_max_duration ) / self.animation_max_duration )
        green = self.intro_animation_start_colour[1] - int( self.blink_difference[1] * ( animation_tick - self.animation_max_duration ) / self.animation_max_duration )
        blue = self.intro_animation_start_colour[2] - int( self.blink_difference[2] * ( animation_tick - self.animation_max_duration ) / self.animation_max_duration )
        red_hex = "0" + format(red, "x") if red <= 15 else format(red, "x")
        green_hex = "0" + format(green, "x") if green <= 15 else format(green, "x")
        blue_hex = "0" + format(blue, "x") if blue <= 15 else format(blue, "x")
        paint.color = red_hex + green_hex + blue_hex

        # Centers of the growing bar
        width_center = self.x + (end_element_width - element_width ) / 2
        height_center = self.y + (end_element_height - element_height ) / 2

        # Offset to keep the bar nicely centered during growth
        x_grow_offset = ( end_element_height - element_height ) / 2
        
        # Draw the expanding GUI
        self.draw_background(canvas, width_center, height_center, element_width, element_height, paint)                                
            
        # Draw a linear /\ animation circle at the start like a TV set    
        circle_animation_duration = 12
        circle_animation_midway_point = circle_animation_duration / 2
        circle_state = -self.animation_max_duration + circle_animation_duration + animation_tick \
            if animation_tick < self.animation_max_duration - circle_animation_midway_point \
            else self.animation_max_duration - circle_animation_midway_point - animation_tick + circle_animation_midway_point
                
        circle_size = end_element_height / 2 * (circle_state / circle_animation_midway_point)
        canvas.draw_circle( self.x + (end_element_width / 2 ), self.y + end_element_height / 2, circle_size, paint)
        return True
        
    def draw_background(self, canvas, origin_x, origin_y, width, height, paint):
        radius = height / 2
        rect = ui.Rect(origin_x, origin_y, width, height)
        rrect = skia.RoundRect.from_rect(rect, x=radius, y=radius)
        canvas.draw_rrect(rrect)
        
    def draw_icon(self, canvas, origin_x, origin_y, diameter, paint, icon ):
        radius = diameter / 2
        canvas.draw_circle( origin_x + radius, origin_y + radius, radius, paint)
        if (icon.image is not None and self.theme.get_image(icon.image) is not None ):
            image = self.theme.get_image(icon.image, diameter, diameter)
            canvas.draw_image(image, origin_x + radius - image.width / 2, origin_y + radius - image.height / 2 )
            
        self.icon_positions.append({"icon": icon, "center_x": origin_x + radius, "center_y": origin_y + radius, "radius": radius})
        
    def reset_blink(self):
        self.blink_state = 0
        self.blink_colour = [0, 0, 0]
        
        mode = self.content.get_variable("mode", "command")
        if mode == "command":
            self.blink_colour = self.command_blink_colour
        elif mode == "dictation":
            self.blink_colour = self.dictation_blink_colour
        elif mode == "sleep":
            self.blink_colour = self.sleep_blink_colour

        self.blink_difference = [
            self.intro_animation_end_colour[0] - self.intro_animation_start_colour[0],
            self.intro_animation_end_colour[1] - self.intro_animation_start_colour[1],
            self.intro_animation_end_colour[2] - self.intro_animation_start_colour[2]
        ]

    def generate_accessible_nodes(self, parent):
        if not self.minimized:
            for icon in self.icons:
                parent.append( self.generate_accessible_node(icon.accessible_text, "button" if icon.callback else "image", path = icon.topic))
        
        parent = self.generate_accessible_context(parent)
        return parent
        
    def activate(self, focus_node = None) -> bool:
        """Implement focus activation"""
        activated = super().activate(focus_node)
        if activated == False:
            if focus_node is None:
                focus_node = self.current_focus

            if focus_node is not None and focus_node.role == "button":
                for icon in self.icons:
                    if focus_node.equals(icon.topic):
                        icon.callback(self, icon)
                        activated = True
        return activated
