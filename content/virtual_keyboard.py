from talon import app, actions, Module, ctrl, cron, ui
from typing import Callable

def in_region(pos, x, y, width, height):
    return pos[0] >= x and pos[0] <= x + width and \
        pos[1] >= y and pos[1] <= y + height

class VirtualKeyboardPoller:
    enabled = False
    content = None
    keyboards = {}
    keyboard_items = []
    toolbar_index = -1
    current_keyboard = None
    null_activation_function = None

    def add_keyboard(self, id, keyboard_items, null_activation_function):
        self.toolbars[id] = {
            "items": toolbar_items,
            "null_activation_function": null_activation_function
        }
        
        if self.enabled and id == self.current_keyboard:
            self.update_keyboard()

    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.update_keyboard()
        
    def set_toolbar(self, keyboard_name:str = None):
        if keyboard_name is not None:        
            self.current_keyboard = keyboard_name
            self.update_keyboard()

    def update_keyboard(self):
        if self.current_keyboard is not None and self.current_keyboard in self.keyboards:
            self.keyboard_items = self.keyboards[self.current_keyboard]["items"]
            self.null_activation_function = self.keyboards[self.current_keyboard]["null_activation_function"]
            self.toolbar_index = -1
            
            # TODO CREATE VIRTUAL KEYBOARD
            #screen_regions = []
            #for keyboard_item in self.keyboard_items:
                #screen_region = self.content.create_screen_region("dwell_toolbar", toolbar_item["colour"], toolbar_item["icon"], toolbar_item["text"], 1, \
                #    toolbar_item["x"], toolbar_item["y"], toolbar_item["width"], toolbar_item["height"], toolbar_item["relative_x"] if "relative_x" in toolbar_item else 0, \
                #    toolbar_item["relative_y"] if "relative_y" in toolbar_item else 0)
                #screen_regions.append(screen_region)
            #self.content.publish_event("screen_regions", "dwell_toolbar", "replace", screen_regions)

    def activate_key(self):
        keyboard_item = self.toolbar_items[self.selected_index] if self.selected_index > -1 and self.selected_index < len(self.keyboard_items) else None
        if keyboard_item is not None:
            keyboard_item["activation_function"]()            
        elif self.null_activation_function is not None:
            self.null_activation_function()

    def disable(self):
        if self.enabled:
            self.enabled = False    
            self.content.publish_event("screen_regions", "virtual_keyboard", "remove")
            self.selected_index = -1

virtual_keyboard_poller = VirtualKeyboardPoller()
def register_virtual_keyboard_poller():
    actions.user.hud_add_poller("virtual_keyboard", virtual_keyboard_poller)

app.register('ready', register_virtual_keyboard_poller)

mod = Module()
@mod.action_class
class Actions:

    def hud_show_virtual_keyboard(keyboard_name: str = None):
        """Show the virtual keyboard screen regions"""
        global virtual_keyboard_poller
        actions.user.hud_activate_poller("virtual_keyboard")
        virtual_keyboard_poller.set_keyboard(keyboard_name)

    def hud_hide_virtual_keyboard():
        """Hide the virtual keyboard screen regions"""
        actions.user.hud_deactivate_poller("virtual_keyboard")
    
    def hud_register_virtual_keyboard(id: str, keyboard_items: list, null_activation: Callable = None):
        """Register a virtual keyboard that can be activated manually"""
        global virtual_keyboard_poller
        if null_activation is None:
            null_activation = lambda: print("No keyboard item selected - Using default activation")
        virtual_keyboard_poller.add_keyboard(id, keyboard_items, null_activation)

    def hud_activate_keyboard():
        """Activate a toolbar item manually"""
        global dwell_toolbar_poller
        dwell_toolbar_poller.activate_key()
