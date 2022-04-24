from talon import app, actions, Module, ctrl, cron, ui
from typing import Callable

def in_region(pos, x, y, width, height):
    return pos[0] >= x and pos[0] <= x + width and \
        pos[1] >= y and pos[1] <= y + height

class DwellToolbarPoller:
    enabled = False
    content = None
    toolbars = {}
    toolbar_items = []
    activate_dwell_job = None
    select_dwell_job = None
    toolbar_index = -1
    selected_index = -1
    toolbar_dwell_ms = 0
    check_interval_ms = 50
    toolbar_select_threshold_ms = 750
    current_toolbar = None
    null_activation_function = None

    def add_toolbar(self, id, toolbar_items, null_activation_function):
        self.toolbars[id] = {
            "items": toolbar_items,
            "null_activation_function": null_activation_function
        }
        
        if self.enabled and id == self.current_toolbar:
            self.update_toolbar()

    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.update_toolbar()
        
    def set_toolbar(self, toolbar_name:str = None):
        if toolbar_name is not None:        
            self.current_toolbar = toolbar_name
            self.update_toolbar()

    def update_toolbar(self):
        if self.current_toolbar is not None and self.current_toolbar in self.toolbars:
            self.toolbar_items = self.toolbars[self.current_toolbar]["items"]
            self.null_activation_function = self.toolbars[self.current_toolbar]["null_activation_function"]
            cron.cancel(self.select_dwell_job)
            self.select_dwell_job = cron.interval(str(self.check_interval_ms) + "ms", self.detect_select_toolbar_item)
            self.toolbar_index = -1
            self.toolbar_dwell_ms = 0
            
            screen_regions = []
            for toolbar_item in self.toolbar_items:
                screen_region = self.content.create_screen_region("dwell_toolbar", toolbar_item["colour"], toolbar_item["icon"], toolbar_item["text"], 1, \
                    toolbar_item["x"], toolbar_item["y"], toolbar_item["width"], toolbar_item["height"], toolbar_item["relative_x"] if "relative_x" in toolbar_item else 0, \
                    toolbar_item["relative_y"] if "relative_y" in toolbar_item else 0)
                screen_regions.append(screen_region)
            self.content.publish_event("screen_regions", "dwell_toolbar", "replace", screen_regions)
    
    def detect_select_toolbar_item(self):
        pos = ctrl.mouse_pos()
        select_threshold = self.toolbar_select_threshold_ms

        # Increment the toolbar items dwell time when it is hovered over the same item
        if self.toolbar_index > -1:
            toolbar_item = self.toolbar_items[self.toolbar_index]
            if in_region(pos, toolbar_item["x"], toolbar_item["y"], toolbar_item["width"], toolbar_item["height"]):
                self.toolbar_dwell_ms += self.check_interval_ms
                if toolbar_item["selection_dwell_ms"] > -1:
                    select_threshold = toolbar_item["selection_dwell_ms"]
            else:
                self.toolbar_index = -1
        
        if self.toolbar_index == -1:
            self.toolbar_dwell_ms = 0
            for index, toolbar_item in enumerate(self.toolbar_items):
                if in_region(pos, toolbar_item["x"], toolbar_item["y"], toolbar_item["width"], toolbar_item["height"]):
                    self.toolbar_index = index
                    break
        
        if self.toolbar_index > -1 and self.toolbar_dwell_ms >= select_threshold:
            self.select_cursor(self.toolbar_index)

    def select_cursor(self, index):
        toolbar_item = self.toolbar_items[index]
        if self.selected_index != index:
            self.selected_index = index
            cron.cancel(self.activate_dwell_job)
            cursor_region = self.content.create_screen_region("toolbar_icon", toolbar_item["colour"], toolbar_item["icon"], toolbar_item["text"], 0)
            self.content.publish_event("cursor_regions", "toolbar_icon", "replace", cursor_region)

            if toolbar_item["activation_dwell_ms"] > 0:
                self.activate_dwell_job = cron.after( str(toolbar_item["activation_dwell_ms"]) + "ms", self.activate_cursor)

    def activate_cursor(self):
        toolbar_item = self.toolbar_items[self.selected_index] if self.selected_index > -1 and self.selected_index < len(self.toolbar_items) else None
        if toolbar_item is not None:
            toolbar_item["activation_function"]()
            
            if not ("keep_alive" in toolbar_item and toolbar_item["keep_alive"] == True):
                self.clear_cursor()
        elif self.null_activation_function is not None:
            self.null_activation_function()
    
    def clear_cursor(self):
        self.content.publish_event("cursor_regions", "toolbar_icon", "remove")
        self.selected_index = -1

    def disable(self):
        if self.enabled:
            self.enabled = False    
            self.content.publish_event("screen_regions", "dwell_toolbar", "remove")
            self.content.publish_event("cursor_regions", "toolbar_icon", "remove")
            self.selected_index = -1
            cron.cancel(self.select_dwell_job)
            cron.cancel(self.activate_dwell_job)

dwell_toolbar_poller = DwellToolbarPoller()
def register_dwell_toolbar_poller():
    actions.user.hud_add_poller("dwell_toolbar", dwell_toolbar_poller)

#app.register('ready', register_dwell_toolbar_poller)

mod = Module()
@mod.action_class
class Actions:

    def hud_show_toolbar(toolbar_name: str = None):
        """Show the toolbar screen regions"""
        global dwell_toolbar_poller
        actions.user.hud_activate_poller("dwell_toolbar")
        dwell_toolbar_poller.set_toolbar(toolbar_name)

    def hud_hide_toolbar():
        """Hide the toolbar screen regions"""
        actions.user.hud_deactivate_poller("dwell_toolbar")
    
    def hud_register_toolbar(id: str, toolbar_items: list, null_activation: Callable = None):
        """Register a toolbar that can be activated with dwell regions"""
        global dwell_toolbar_poller
        if null_activation is None:
            null_activation = lambda: print("No toolbar item selected - Using default activation")
        dwell_toolbar_poller.add_toolbar(id, toolbar_items, null_activation)
        
    def hud_create_toolbar_item(x:int = 100, y:int = 100, width:int = 150, height:int = 150, icon: str = None, colour: str = None, text: str = None, activation_function: Callable = None, selection_dwell_ms:int = -1, activation_dwell_ms:int = -1, keep_alive:int = 0):
        """Create an item for the dwell toolbar that will be used inside of a single toolbar"""
        if activation_function is None:
            activation_function = lambda: print("Activating toolbar item at x" + str(x))
        return {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "icon": icon,
            "colour": "FFFFFF" if colour is None else colour,
            "text": text,
            "selection_dwell_ms": selection_dwell_ms,
            "activation_dwell_ms": activation_dwell_ms,
            "activation_function": activation_function,
            "keep_alive": keep_alive != 0
        }

    def hud_activate_toolbar_item():
        """Activate a toolbar item manually"""
        global dwell_toolbar_poller
        dwell_toolbar_poller.activate_cursor()

    def hud_clear_toolbar_item():
        """Clear the currently selected toolbar item"""
        global dwell_toolbar_poller
        dwell_toolbar_poller.clear_cursor()

