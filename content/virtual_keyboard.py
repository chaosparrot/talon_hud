from talon import app, actions, Module, ctrl, cron, ui
from typing import Callable, Union
from .dwell_toolbar import in_region, default_colour_scheme, layout_virtual_key

class VirtualKeyboardPoller:
    enabled = False
    content = None
    keyboards = {}
    keyboard_items = []
    current_keyboard = None
    monitor_index = 0

    def add_keyboard(self, id, virtual_keys, layout_style: str = 'full', alignment: str = 'top', horizontal_key_amount: int = 3, vertical_key_amount: int = 3, visible: bool = True):
        key_amount = len(virtual_keys)
        while key_amount > horizontal_key_amount * vertical_key_amount:
            if horizontal_key_amount <= vertical_key_amount:
                horizontal_key_amount += 1
            else:
                vertical_key_amount += 1
    
        self.keyboards[id] = {
            "virtual_keys": virtual_keys,
            "hover_visibility": 1,
            "layout_style": layout_style,
            "alignment": alignment,
            "horizontal_key_amount": horizontal_key_amount,
            "vertical_key_amount": vertical_key_amount,
            "visible": visible,
        }
        
        if self.enabled and id == self.current_keyboard:
            self.update_keyboard()        

    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.update_keyboard()
            ui.register("screen_change", self.update_keyboard)            

    def disable(self):
        if self.enabled:
            self.enabled = False    
            self.content.publish_event("screen_regions", "virtual_keyboard", "remove")
            self.selected_index = -1
            ui.unregister("screen_change", self.update_keyboard)

    def set_keyboard(self, name:str = None, monitor: int = 0, visible: bool = True):
        if name is not None and self.enabled:        
            self.current_keyboard = name
            self.monitor_index = monitor
            if self.current_keyboard is not None and self.current_keyboard in self.keyboards:
                self.keyboards[self.current_keyboard]["visible"] = visible
            self.update_keyboard()

    def update_keyboard(self):
        global default_colour_scheme    
        if self.current_keyboard is not None and self.current_keyboard in self.keyboards:
        
            # Determine the base layout parameters
            screens = ui.screens()
            if self.monitor_index >= len(screens):
                self.monitor_index = 0
            horizontal_amount = self.keyboards[self.current_keyboard]["horizontal_key_amount"]
            vertical_amount = self.keyboards[self.current_keyboard]["vertical_key_amount"]
            layout_style = self.keyboards[self.current_keyboard]["layout_style"]
            alignment = self.keyboards[self.current_keyboard]["alignment"]
            grid_width = int(round(screens[self.monitor_index].rect.width / horizontal_amount))
            grid_height = int(round(screens[self.monitor_index].rect.height / vertical_amount))
            
            screen_regions = []
            keyboard_items = []
            layout_index = 0
            colour_index = 0
            
            # Layout all the virtual keys
            for virtual_key in self.keyboards[self.current_keyboard]["virtual_keys"]:
                virtual_key["rect"] = layout_virtual_key(virtual_key, layout_index, layout_style, alignment, grid_width, grid_height, horizontal_amount, vertical_amount)
                virtual_key["rect"].x += screens[self.monitor_index].rect.x
                virtual_key["rect"].y += screens[self.monitor_index].rect.y                
                if virtual_key["width"] == -1 or virtual_key["height"] == -1:
                    layout_index += 1
                
                # Determine a colour
                background_colour = ''
                text_colour = ''
                if "colour" not in virtual_key or not virtual_key["colour"]:
                    background_colour = default_colour_scheme[colour_index]["background"]
                    text_colour = default_colour_scheme[colour_index]["text"]
                    colour_index += 1
                else:
                    background_colour = virtual_key["colour"]
                    text_colour = virtual_key["text_colour"] if "text_colour" in virtual_key and virtual_key["text_colour"] else ''
                virtual_key["colour"] = background_colour
                virtual_key["text_colour"] = text_colour
                
                # Create the screen region content
                if self.keyboards[self.current_keyboard]["visible"]:
                    screen_region = self.content.create_screen_region("virtual_keyboard", background_colour, \
                        virtual_key["icon"], virtual_key["text"], self.keyboards[self.current_keyboard]["hover_visibility"], \
                        virtual_key["rect"].x, virtual_key["rect"].y, virtual_key["rect"].width, virtual_key["rect"].height, virtual_key["relative_x"] if "relative_x" in virtual_key else 0, \
                        virtual_key["relative_y"] if "relative_y" in virtual_key else 0)
                    if text_colour:
                        screen_region.text_colour = text_colour
                    screen_regions.append(screen_region)
                
                # Add the virtual key to the active keyboard items
                keyboard_items.append(virtual_key)
            
            self.content.publish_event("screen_regions", "virtual_keyboard", "replace", screen_regions)
            self.keyboard_items = keyboard_items            

    def activate_key(self):
        pos = ctrl.mouse_pos()
        
        key_index = -1
        for index, keyboard_item in enumerate(self.keyboard_items):
            if in_region(pos, keyboard_item["rect"].x, keyboard_item["rect"].y, keyboard_item["rect"].width, keyboard_item["rect"].height):
                key_index = index
                break
    
        keyboard_item = self.keyboard_items[key_index] if key_index > -1 and key_index < len(self.keyboard_items) else None
        if keyboard_item is not None:
            keyboard_item["callback"]()

    def set_visibility(self, visible: bool):
        if self.current_keyboard is not None and self.current_keyboard in self.keyboards:
            self.keyboards[self.current_keyboard]["visible"] = visible
            self.update_keyboard()

virtual_keyboard_poller = VirtualKeyboardPoller()
def register_virtual_keyboard_poller():
    actions.user.hud_add_poller("virtual_keyboard", virtual_keyboard_poller)

app.register('ready', register_virtual_keyboard_poller)

mod = Module()
@mod.action_class
class Actions:

    def hud_set_virtual_keyboard(name: str = None, monitor: int = 0, visible: Union[bool, int] = True):
        """Show the virtual keyboard screen regions"""
        global virtual_keyboard_poller
        if name is None or name == '':
            actions.user.hud_deactivate_poller("virtual_keyboard")
        else:
            actions.user.hud_activate_poller("virtual_keyboard")
            virtual_keyboard_poller.set_keyboard(name, monitor, visible)
    
    def hud_register_virtual_keyboard(name: str, virtual_keys: list, layout_style: str = 'full', alignment: str = 'top', horizontal_key_amount: int = 3, vertical_key_amount: int = 3):
        """Register a virtual keyboard that can be activated manually"""
        global virtual_keyboard_poller
        virtual_keyboard_poller.add_keyboard(name, virtual_keys, layout_style, alignment, horizontal_key_amount, vertical_key_amount)

    def hud_activate_virtual_key():
        """Activate a virtual keyboard key manually"""
        global virtual_keyboard_poller
        virtual_keyboard_poller.activate_key()

    def hud_set_virtual_keyboard_visibility(visible: Union[bool, int] = True):
        """Set the visibility of the current dwell toolbar"""
        global virtual_keyboard_poller
        virtual_keyboard_poller.set_visibility(visible)