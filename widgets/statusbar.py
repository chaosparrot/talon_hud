from ..base_widget import BaseWidget
from ..utils import linear_gradient
from ..widget_preferences import HeadUpDisplayUserWidgetPreferences
from ..content.typing import HudButton
from talon import skia, ui, Module, cron, actions
import time
import numpy

def add_focus_icon(widget):
    if "focus_indicator" not in widget.subscribed_content:    
        widget.subscribed_content.append("focus_indicator")
    actions.user.hud_toolkit_focus()

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
    subscribed_content = [
        "mode",
        "programming_language",
        "status_icons",
    ]

    # New content topic types
    topic_types = ['status_icons', 'status_options']
    current_topics = ["mode_icon"]
    subscriptions = ["*"]

    content = {
        'mode': 'command',
        'language': 'en_US', 
        'programming_language': {
            'ext': None,
            'forced': False
        },
        "status_icons": []
    }
    
    animation_max_duration = 60
    
    def refresh(self, new_content):
        if (self.animation_tick == 0 and "mode" in new_content and new_content["mode"] != self.content['mode']):            
            if (new_content["mode"] == 'command'):
                self.blink_colour = self.command_blink_colour
            elif (new_content["mode"] == 'dictation'):
                self.blink_colour = self.dictation_blink_colour
            elif (new_content["mode"] == 'sleep'):
                self.blink_colour = self.sleep_blink_colour
            elif (new_content["mode"] == 'parrot_switch'):
                self.blink_colour = self.parrot_blink_colour
            
            # Calculate the colour difference between the blink and the next state
            # To make it easier to calculate during draw
            self.blink_difference = [
                self.background_colour[0] - self.blink_colour[0],
                self.background_colour[1] - self.blink_colour[1],
                self.background_colour[2] - self.blink_colour[2]
            ]
        
            self.blink_state = 100 if self.show_animations else 0        
        self.update_icons(new_content)
        self.update_buttons()
    
    def update_buttons(self):
        buttons = []
        buttons.append(HudButton("", "Content toolkit", ui.Rect(0,0,0,0), lambda widget: actions.user.hud_toolkit_options()))
        buttons.append(HudButton("microphone_on", "Add microphone", ui.Rect(0,0,0,0), lambda widget: actions.user.hud_add_single_click_mic_toggle()))
        buttons.append(HudButton("en_US", "Add language", ui.Rect(0,0,0,0), lambda widget: actions.user.hud_add_language_toggle()))        
        buttons.append(HudButton("focus", "Add focus indicator", ui.Rect(0,0,0,0), lambda widget: actions.user.hud_add_focus_toggle()))
        
        if "active_microphone" in self.subscribed_content:
            buttons[1].text = "Remove microphone"
            buttons[1].callback = lambda widget: actions.user.hud_remove_single_click_mic_toggle()
            
        if "language" in self.subscribed_content:
            buttons[2].text = "Remove language"
            buttons[2].callback = lambda widget: actions.user.hud_remove_language_toggle()

        if "focus_indicator" in self.subscribed_content:
            buttons[3].text = "Remove focus indicator"
            buttons[3].callback = lambda widget: actions.user.hud_remove_focus_toggle()
        
        self.buttons = buttons
    
    def update_icons(self, new_content):
        mode = self.content["mode"] if "mode" not in new_content else new_content["mode"]
    
        self.icons = [{
            "id": "mode",
            "image": mode + "_icon",
            "clickable": mode != "sleep"
        }]
        
        if "active_microphone" in self.subscribed_content and "active_microphone" in new_content and new_content["active_microphone"]:
            self.icons.append({
                "id": "microphone",
                "image": "microphone_off" if new_content["active_microphone"] == "None" else "microphone_on",
                "clickable": True
            })
                
        if "language" in self.subscribed_content:
            language = self.content["language"] if "language" not in new_content else new_content["language"]
            
            self.icons.append({
                "id": "language", 
                "image": language,
                "clickable": language != 'en_US'
            })
            
        if "focus_indicator" in self.subscribed_content:
            self.icons.append({
                "id": "focus_indicator",
                "image": "focus",
                "clickable": True
            })

            
        status_icons = self.content["status_icons"] if "status_icons" not in new_content else new_content['status_icons']
        for status_icon in status_icons:
            self.icons.append(status_icon)
        
    def on_mouse(self, event):
        pos = numpy.array(event.gpos)
        
        # Hit detection of buttons        
        hover_index = -1
        for index, icon in enumerate(self.icon_positions):
            if (numpy.linalg.norm(pos - numpy.array([icon['center_x'], icon['center_y']])) < icon['radius']):
                hover_index = index
                break
        
        if (event.event == "mousemove"):
            # Only resume for a frame if our button state has changed
            if (self.icon_hover_index != hover_index):
                self.icon_hover_index = hover_index                
                self.canvas.resume()
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
            actions.user.activate_statusbar_icon(self.icon_positions[self.icon_hover_index]['icon']['id'])
        self.icon_hover_index = -1
                
    def enable(self, persist=False):
        if not self.enabled:
            self.reset_blink()
            self.update_icons({})
            self.update_buttons()
            super().enable(persist)
    
    def load_theme_values(self):
        self.command_blink_colour = self.theme.get_colour_as_ints('command_blink_colour')
        self.sleep_blink_colour = self.theme.get_colour_as_ints('sleep_blink_colour')
        self.dictation_blink_colour = self.theme.get_colour_as_ints('dictation_blink_colour')
        self.parrot_blink_colour = self.theme.get_colour_as_ints('parrot_blink_colour')
        self.background_colour = self.theme.get_colour_as_ints('background_colour')
        self.intro_animation_start_colour = self.theme.get_colour_as_ints('intro_animation_start_colour')
        self.intro_animation_end_colour = self.theme.get_colour_as_ints('intro_animation_end_colour')
        self.reset_blink()
    
    def draw(self, canvas) -> bool:
        paint = self.draw_setup_mode(canvas)
        self.icon_positions = []
        stroke_width = 1.5
        circle_margin = 4
        element_height = self.height - ( stroke_width * 2 )
        icon_diameter = self.height - ( circle_margin * 2 )
        element_width = self.width 
        
        # Draw the background with bigger stroke than 1px
        stroke_colours = (self.theme.get_colour('top_stroke_colour'), self.theme.get_colour('down_stroke_colour'))
        paint.shader = linear_gradient(self.x, self.y, self.x, self.y + element_height * 2, stroke_colours)
        self.draw_background(canvas, self.x, self.y, element_width, element_height + (stroke_width * 2), paint)
        
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
        red_hex = '0' + format(red, 'x') if red <= 15 else format(red, 'x')
        green_hex = '0' + format(green, 'x') if green <= 15 else format(green, 'x')
        blue_hex = '0' + format(blue, 'x') if blue <= 15 else format(blue, 'x')
        
        # Draw the background based on the state
        accent_colour = red_hex + green_hex + blue_hex
        mode_colour = self.theme.get_colour( self.content["mode"] + '_mode_colour')
        background_shader = linear_gradient(self.x, self.y, self.x, self.y + element_height * 2, (mode_colour, accent_colour))
        paint.shader = background_shader
        self.draw_background(canvas, self.x + stroke_width, self.y + stroke_width, element_width - stroke_width * 2, element_height, paint)

        # Draw icons
        for index, icon in enumerate(self.icons):
            if (not icon['clickable']):
                paint.shader = background_shader
            else:
                button_colour = self.theme.get_colour('button_hover_colour') if self.icon_hover_index == index else self.theme.get_colour('button_colour')
                paint.shader = linear_gradient(self.x, self.y, self.x, self.y + element_height, (self.theme.get_colour('button_colour'), button_colour))
            
            # Do not draw icons or buttons without a valid image
            if icon['image'] is not None and self.theme.get_image(icon['image']) is not None:
                self.draw_icon(canvas, self.x + stroke_width + circle_margin + ( index * icon_diameter ) + ( index * circle_margin ), self.y + circle_margin, icon_diameter, paint, icon)

        height_center = self.y + element_height + ( circle_margin / 2 ) - ( element_height / 2 )

        # Draw selected programming language
        # TODO - FAKE BOLD until I find out how to properly use font style
        if ((self.content["mode"] == "command" and self.content["programming_language"]["ext"] is not None) or self.content["mode"] == "dictation"):
            text_colour =  self.theme.get_colour('text_forced_colour') if self.content["programming_language"]["forced"] else self.theme.get_colour('text_colour')
            paint.shader = linear_gradient(self.x, self.y, self.x, self.y + element_height, (text_colour, text_colour))
            paint.style = paint.Style.STROKE
            paint.textsize = self.font_size
            text_x = self.x + circle_margin * 2 + ( len(self.icons) * ( icon_diameter + circle_margin ) )
            canvas.draw_text(self.content["programming_language"]["ext"] if self.content["mode"] == "command" else "Dictate", text_x , height_center - circle_margin + paint.textsize / 2)
            paint.style = paint.Style.FILL
            canvas.draw_text(self.content["programming_language"]["ext"] if self.content["mode"] == "command" else "Dictate", text_x, height_center - circle_margin + paint.textsize / 2)

        # Draw closing icon
        paint.style = paint.Style.FILL
        close_colour = self.theme.get_colour('close_icon_hover_colour') if self.icon_hover_index == len(self.icons) else self.theme.get_colour('close_icon_accent_colour')
        paint.shader = linear_gradient(self.x, self.y, self.x, self.y + element_height, (self.theme.get_colour('close_icon_colour'), close_colour))
        close_icon_diameter = icon_diameter / 2
        self.draw_icon(canvas, self.x + element_width - close_icon_diameter - close_icon_diameter / 2 - stroke_width, height_center - close_icon_diameter / 2, close_icon_diameter, paint, {'id': 'close', 'image': None})

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
        red_hex = '0' + format(red, 'x') if red <= 15 else format(red, 'x')
        green_hex = '0' + format(green, 'x') if green <= 15 else format(green, 'x')
        blue_hex = '0' + format(blue, 'x') if blue <= 15 else format(blue, 'x')
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
        if (icon['image'] is not None and self.theme.get_image(icon['image']) is not None ):
            image = self.theme.get_image(icon['image'], diameter, diameter)
            canvas.draw_image(image, origin_x + radius - image.width / 2, origin_y + radius - image.height / 2 )
                
        self.icon_positions.append({'icon': icon, 'center_x': origin_x + radius, 'center_y': origin_y + radius, 'radius': radius})
        
    def reset_blink(self):
        self.blink_state = 0
        self.blink_colour = [0, 0, 0]
        self.blink_difference = [
            self.intro_animation_end_colour[0] - self.intro_animation_start_colour[0],
            self.intro_animation_end_colour[1] - self.intro_animation_start_colour[1],
            self.intro_animation_end_colour[2] - self.intro_animation_start_colour[2]
        ]

previous_microphone = "System Default"
mod = Module()
@mod.action_class
class Actions:

    def hud_add_language_toggle():
        """Add the language icon to the status bar"""
        actions.user.hud_widget_subscribe_topic("status_bar", "language")
        actions.user.hud_refresh_content()
        
    def hud_remove_language_toggle():
        """Removes the language icon from the status bar"""
        actions.user.hud_widget_unsubscribe_topic("status_bar", "language")
        actions.user.hud_refresh_content()
        
    def hud_add_focus_toggle():
        """Add the focus indicator icon to the status bar"""
        actions.user.hud_widget_subscribe_topic("status_bar", "focus_indicator")
        actions.user.hud_add_focus_indicator()
        actions.user.hud_refresh_content()        
        
    def hud_remove_focus_toggle():
        """Removes the focus indicator icon from the status bar"""
        actions.user.hud_widget_unsubscribe_topic("status_bar", "focus_indicator")
        actions.user.hud_remove_focus_indicator()        
        actions.user.hud_refresh_content()
    
    def activate_statusbar_icon(id: str):
        """Activate an icon on the status bar"""
        if (id == "mode"):
            actions.speech.disable()
        elif (id == "language"):
            # TODO THIS NO LONGER SEEMS TO WOKR?
            actions.speech.switch_language('en_US')
        elif (id == "microphone"):
            global previous_microphone
            
            current_microphone = actions.sound.active_microphone()
            if current_microphone != "None":
                actions.sound.set_microphone("None")
                previous_microphone = current_microphone
            else:
                if previous_microphone == "None":
                    previous_microphone = "System Default"
                actions.sound.set_microphone(previous_microphone)
        elif (id == "focus_indicator"):
            actions.user.hud_remove_focus_toggle()
                
        elif (id == "close"):
            actions.user.disable_hud()
