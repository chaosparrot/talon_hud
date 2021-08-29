from user.talon_hud.base_widget import BaseWidget
from talon import skia, ui, Module, cron, actions
import time
import numpy
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import lighten_hex_colour
from copy import copy

class HeadUpAbilityBar(BaseWidget):

    subscribed_content = ["mode", "abilities"]
    content = {
        'mode': 'command',
        "abilities": [            
        ]
    }
    allowed_setup_options = ["position", "dimension", "limit"]

    # By default - This widget sits to the left side of the status bar
    preferences = HeadUpDisplayUserWidgetPreferences(type="ability_bar", x=1120, y=934, width=500, height=80, enabled=True, alignment="right", expand_direction="up", font_size=18)
    animation_max_duration = 60
    ttl_poller = None

    def disable(self, persisted=False):
        if self.enabled:
            super().disable(persisted)
            cron.cancel(self.ttl_poller)
            self.ttl_poller = None
            
    def enable(self, persisted=False):
        if not self.enabled:
            super().enable(persisted)

    def draw(self, canvas) -> bool:
        paint = self.draw_setup_mode(canvas)
        
        diameter = self.height / 2
        abilities = copy(self.content['abilities'])
        if self.alignment == "right":
            abilities.reverse()
        margin = 4
        origin = self.x if self.alignment == "left" else self.x + self.width - diameter        
        offset = diameter + margin if self.alignment == "left" else -(diameter + margin)
        
        continue_drawing = False
        for index, ability in enumerate(abilities):
            continue_drawing = self.draw_ability(canvas, origin + ( offset * index ), self.y, diameter, paint, ability) or continue_drawing
        return continue_drawing

    def draw_ability(self, canvas, origin_x, origin_y, diameter, paint, ability ):
        radius = diameter / 2
        animating = False
                
        opacity = int('FF' if ability['colour'] is None or len(ability['colour']) < 8 else ability['colour'][-2:], 16) / 255
        opacity_value = int(opacity / 6 * 255) if ability['enabled'] == False else int(opacity * 255)
        opacity_hex = '0' + format(opacity_value, 'x') if opacity_value <= 15 else format(opacity_value, 'x')        
        
        if ability['colour'] is not None:
            colour = list( self.theme.get_colour(ability['colour'], ability['colour']) )
            colour[6:] = opacity_hex
            paint.color = "".join(colour)
            canvas.draw_circle( origin_x + radius, origin_y + radius, radius, paint)
        
        if (ability['image'] is not None and self.theme.get_image(ability['image']) is not None ):
            paint.color = opacity_value
            image = self.theme.get_image(ability['image'])
            
            offset_x = 0 if 'image_offset_x' not in ability else ability['image_offset_x']
            offset_y = 0 if 'image_offset_y' not in ability else ability['image_offset_y']            
            canvas.draw_image(image, origin_x + radius - image.width / 2 + offset_x, origin_y + radius - image.height / 2 + offset_y)
            
        if ability['activated'] > 0:
            paint.color = self.theme.get_colour("ability_activation_colour", "FFFFFFAA")
            canvas.draw_circle( origin_x + radius, origin_y + radius, radius, paint)
            ability['activated'] = ability['activated'] - 1
            animating = True
        
        return animating
        
    def draw_animation(self, canvas, animation_tick):
        return True