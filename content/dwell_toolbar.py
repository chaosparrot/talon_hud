from talon import app, actions, Module, ctrl, cron, ui
from typing import Callable, Union
import math

# Colour schemes uses from https://personal.sron.nl/~pault/ made by Paul Tol
# A mix and match of different schemes, which I know isn't the best thing to do given that the schemes should work on their own
# But we are dealing with cases where the amount of possible options is larger than the given schemes
paul_tol_schemes = [
    # Paul Tol scheme 1
    {"background": "4477AA", "text": "EEEEEE"},
    {"background": "66CCEE", "text": "000000"},
    {"background": "228833", "text": "EEEEEE"},
    {"background": "CCBB44", "text": "000000"},
    {"background": "EE6677", "text": "000000"}, 
    {"background": "AA3377", "text": "EEEEEE"},
    {"background": "AAAAAA", "text": "000000"},
    {"background": "FFFFFF", "text": "000000"},
    {"background": "000000", "text": "EEEEEE"},
    # Paul Tol scheme 1 figure 3
    {"background": "EE7733", "text": "000000"}, # Orange
    {"background": "CC3311", "text": "EEEEEE"}, # Red
    # Paul Tol scheme 1 figure 4
    {"background": "332288", "text": "EEEEEE"}, # Indigo
    {"background": "44AA99", "text": "000000"}, # Teal
    {"background": "999933", "text": "000000"}, # Olive
    {"background": "882255", "text": "EEEEEE"}, # Wine
    {"background": "DDDDDD", "text": "000000"}, # Pale grey
    # Paul Tol scheme 1 figure 5
    {"background": "EECC66", "text": "000000"}, # Light yellow
    {"background": "004488", "text": "EEEEEE"}, # Dark blue
]

# Append three layers of opacity to the colour schemes to loop them around, giving a total of 54 possible options
default_colour_scheme = []
for alpha_index in range(0, 2):
    for scheme in paul_tol_schemes:
        if alpha_index == 0:
            default_colour_scheme.append({"background": scheme["background"] + "", "text": scheme["text"] + ""})
        elif alpha_index == 1:
            default_colour_scheme.append({"background": scheme["background"] + "BB", "text": scheme["text"] + ""})
        elif alpha_index == 2:
            default_colour_scheme.append({"background": scheme["background"] + "77", "text": scheme["text"] + ""})        

def in_region(pos, x, y, width, height):
    return pos[0] >= x and pos[0] <= x + width and \
        pos[1] >= y and pos[1] <= y + height

def layout_virtual_key(virtual_key, index, layout_style, alignment, grid_width, grid_height, horizontal_amount, vertical_amount):
    # Dynamic layout
    if virtual_key["width"] == -1 or virtual_key["height"] == -1:
        x = 0
        y = 0
        
        # The full layout uses the complete screen real estate
        if layout_style == "full":
            if alignment == "left":
                x = math.floor(index / vertical_amount) * grid_width
                y = ( index % vertical_amount ) * grid_height
            elif alignment == "right":
                x = grid_width * (horizontal_amount - 1) - math.floor(index / vertical_amount) * grid_width
                y = ( index % vertical_amount ) * grid_height
            elif alignment == "top":
                x = ( index % horizontal_amount ) * grid_width
                y = math.floor(index / vertical_amount) * grid_height
            elif alignment == "bottom":
                x = ( index % horizontal_amount ) * grid_width
                y = grid_height * (vertical_amount - 1) - math.floor(index / vertical_amount) * grid_height
        
        # The open layout tries to wrap around the screen
        # Tested this with 3x3, 4x4, 5x5 and 6x5 grids - Can probably be made prettier but works in all alignments as is
        elif layout_style == "open":
            if alignment in ["left", "right"]:
                # Wrap the vertical side of the screen
                if index < vertical_amount:
                    y = ( index % vertical_amount ) * grid_height
                    if alignment == "right":
                        x = grid_width * (horizontal_amount - 1)
                # Use the top of the screen
                elif index >= vertical_amount and index < vertical_amount + horizontal_amount - 1:
                    y = 0
                    x = ((index + 1 - vertical_amount ) % horizontal_amount) * grid_width
                    # Flip the direction and add the total grid offset
                    if alignment == "right":
                        x = -x + (grid_width * (horizontal_amount - 1))
                
                # Use the opposite vertical side of the screen
                elif index >= vertical_amount + horizontal_amount - 1 and index < vertical_amount + (horizontal_amount * 2 ) - 3:
                    x = grid_width * (horizontal_amount - 1) if alignment == "left" else 0
                    y = (( index - (vertical_amount + horizontal_amount - 1) + 1) % vertical_amount ) * grid_height
                    
                # Use the bottom of the screen
                elif index >= vertical_amount + (horizontal_amount * 2 ) - 3 and index < vertical_amount * 2 + (horizontal_amount - 2) * 2:
                    y = grid_height * (vertical_amount - 1)
                    x = ((index + 1 - (vertical_amount + (horizontal_amount * 2 ) - 3) ) % horizontal_amount) * grid_width
                    # Flip the direction and add the total grid offset
                    if alignment == "right":
                        x = -x + (grid_width * (horizontal_amount - 1))
                
                # Start using the center in the same rotation
                else:
                    new_index = index - ( vertical_amount * 2 + (horizontal_amount - 2) * 2 )
                    rect = self.layout_virtual_key(virtual_key, new_index, layout_style, alignment, grid_width, grid_height, horizontal_amount - 2, vertical_amount - 2)
                    x = rect.x + grid_width
                    y = rect.y + grid_height
            elif alignment in ["top", "bottom"]:
                # First horizontal line
                if index < horizontal_amount:
                    x = ( index % horizontal_amount ) * grid_width
                    y = 0 if alignment == "top" else ( vertical_amount - 1 ) * grid_height
                # Left vertical line
                elif index >= horizontal_amount and index < vertical_amount + horizontal_amount - 1:
                    x = 0
                    y = ((index + 1 - horizontal_amount ) % vertical_amount) * grid_height
                    # Flip the direction and add the total grid offset
                    if alignment == "bottom":
                        y = -y + (grid_height * (vertical_amount - 1))
                # Right vertical line
                elif index >= vertical_amount + horizontal_amount - 1 and index < vertical_amount + ( horizontal_amount - 1 ) * 2:
                    x = (horizontal_amount - 1 ) * grid_width
                    y = ((index + 1 - (vertical_amount + horizontal_amount - 1) ) % vertical_amount) * grid_height
                    # Flip the direction and add the total grid offset
                    if alignment == "bottom":
                        y = -y + (grid_height * (vertical_amount - 1))
                # Opposite horizontal line
                elif index >= vertical_amount + (horizontal_amount - 1) * 2 and index < vertical_amount * 2 + ( horizontal_amount ) * 2 - 4:
                    y = 0 if alignment == "bottom" else ( vertical_amount - 1 ) * grid_height
                    x = ((index + 1 - (vertical_amount + ( horizontal_amount - 1 ) * 2)) % horizontal_amount) * grid_width
                # Start using the center in the same rotation
                else:
                    new_index = index - ( vertical_amount * 2 + (horizontal_amount - 2) * 2 )
                    rect = layout_virtual_key(virtual_key, new_index, layout_style, alignment, grid_width, grid_height, horizontal_amount - 2, vertical_amount - 2)
                    x = rect.x + grid_width
                    y = rect.y + grid_height
        return ui.Rect(x, y, grid_width, grid_height)
    # Static position
    else:
        return ui.Rect(virtual_key["x"], virtual_key["y"], virtual_key["width"], virtual_key["height"])


class DwellToolbarPoller:
    enabled = False
    content = None
    toolbars = {}
    toolbar_items = []
    select_dwell_job = None
    toolbar_index = -1
    selected_index = -1
    toolbar_dwell_ms = 0
    check_interval_ms = 50
    monitor_index = 0
    toolbar_select_threshold_ms = 750
    current_toolbar = None
    null_activation_function = None

    def add_toolbar(self, id, virtual_keys, dwell_ms: int = 750, layout_style: str = 'open', alignment: str = 'left', horizontal_key_amount: int = 3, vertical_key_amount: int = 5, visible: bool = True):
        key_amount = len(virtual_keys)
        while key_amount > horizontal_key_amount * vertical_key_amount:
           horizontal_key_amount += 1
    
        self.toolbars[id] = {
            "virtual_keys": virtual_keys,
            "dwell_ms": dwell_ms,
            "hover_visibility": 1,
            "layout_style": layout_style,
            "alignment": alignment,
            "horizontal_key_amount": horizontal_key_amount,
            "vertical_key_amount": vertical_key_amount,
            "visible": visible
        }
        
        if self.enabled and id == self.current_toolbar:
            self.update_toolbar()

    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.update_toolbar()
            ui.register("screen_change", self.update_toolbar)

    def disable(self):
        if self.enabled:
            self.enabled = False    
            self.content.publish_event("screen_regions", "dwell_toolbar", "remove")
            self.content.publish_event("cursor_regions", "toolbar_icon", "remove")
            self.selected_index = -1
            cron.cancel(self.select_dwell_job)
            ui.unregister("screen_change", self.update_toolbar)

    def set_toolbar(self, toolbar_name:str = None, monitor: int = 0, visible: bool = True):
        if toolbar_name is not None and self.enabled:
            self.current_toolbar = toolbar_name
            if self.current_toolbar is not None and self.current_toolbar in self.toolbars:
                self.toolbars[self.current_toolbar]["visible"] = visible
            self.monitor_index = monitor
            self.update_toolbar()

    def update_toolbar(self):
        global default_colour_scheme
        if self.current_toolbar is not None and self.current_toolbar in self.toolbars:
            cron.cancel(self.select_dwell_job)
            self.select_dwell_job = cron.interval(str(self.check_interval_ms) + "ms", self.detect_select_toolbar_item)
            self.toolbar_index = -1
            self.toolbar_dwell_ms = 0
            self.toolbar_select_threshold_ms = self.toolbars[self.current_toolbar]["dwell_ms"]
            
            # Determine the base layout parameters
            screens = ui.screens()
            if self.monitor_index >= len(screens):
                self.monitor_index = 0
            horizontal_amount = self.toolbars[self.current_toolbar]["horizontal_key_amount"]
            vertical_amount = self.toolbars[self.current_toolbar]["vertical_key_amount"]
            layout_style = self.toolbars[self.current_toolbar]["layout_style"]
            alignment = self.toolbars[self.current_toolbar]["alignment"]
            grid_width = int(round(screens[self.monitor_index].rect.width / horizontal_amount))
            grid_height = int(round(screens[self.monitor_index].rect.height / vertical_amount))
            
            screen_regions = []
            toolbar_items = []
            layout_index = 0
            colour_index = 0
            
            # Layout all the virtual keys
            for virtual_key in self.toolbars[self.current_toolbar]["virtual_keys"]:
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
                if self.toolbars[self.current_toolbar]["visible"]:
                    screen_region = self.content.create_screen_region("dwell_toolbar", background_colour, \
                        virtual_key["icon"], virtual_key["text"], self.toolbars[self.current_toolbar]["hover_visibility"], \
                        virtual_key["rect"].x, virtual_key["rect"].y, virtual_key["rect"].width, virtual_key["rect"].height, virtual_key["relative_x"] if "relative_x" in virtual_key else 0, \
                        virtual_key["relative_y"] if "relative_y" in virtual_key else 0)
                    if text_colour:
                        screen_region.text_colour = text_colour
                
                    screen_regions.append(screen_region)
                
                # Add the virtual key to the active toolbar items
                toolbar_items.append(virtual_key)
            
            self.content.publish_event("screen_regions", "dwell_toolbar", "replace", screen_regions)
            self.toolbar_items = toolbar_items

    def detect_select_toolbar_item(self):
        pos = ctrl.mouse_pos()
        select_threshold = self.toolbar_select_threshold_ms

        # Increment the toolbar items dwell time when it is hovered over the same item
        if self.toolbar_index > -1:
            toolbar_item = self.toolbar_items[self.toolbar_index]
            if in_region(pos, toolbar_item["rect"].x, toolbar_item["rect"].y, toolbar_item["rect"].width, toolbar_item["rect"].height):
                self.toolbar_dwell_ms += self.check_interval_ms
            else:
                self.toolbar_index = -1
        
        if self.toolbar_index == -1:
            self.toolbar_dwell_ms = 0
            for index, toolbar_item in enumerate(self.toolbar_items):
                if in_region(pos, toolbar_item["rect"].x, toolbar_item["rect"].y, toolbar_item["rect"].width, toolbar_item["rect"].height):
                    self.toolbar_index = index
                    break
        
        if self.toolbar_index > -1 and self.toolbar_dwell_ms >= select_threshold:
            self.select_cursor(self.toolbar_index)

    def select_cursor(self, index):
        toolbar_item = self.toolbar_items[index]
        if self.selected_index != index:
            self.selected_index = index
            cursor_region = self.content.create_screen_region("toolbar_icon", toolbar_item["colour"], toolbar_item["icon"], toolbar_item["text"], 0)
            self.content.publish_event("cursor_regions", "toolbar_icon", "replace", cursor_region)

    def activate_cursor(self):
        toolbar_item = self.toolbar_items[self.selected_index] if self.selected_index > -1 and self.selected_index < len(self.toolbar_items) else None
        if toolbar_item is not None:
            toolbar_item["callback"]()
    
    def clear_cursor(self):
        self.content.publish_event("cursor_regions", "toolbar_icon", "remove")
        self.selected_index = -1
        
    def set_visibility(self, visible: bool):
        if self.current_toolbar is not None and self.current_toolbar in self.toolbars:
            self.toolbars[self.current_toolbar]["visible"] = visible
            self.update_toolbar()

dwell_toolbar_poller = DwellToolbarPoller()
def register_dwell_toolbar_poller():
    actions.user.hud_add_poller("dwell_toolbar", dwell_toolbar_poller)

app.register('ready', register_dwell_toolbar_poller)

mod = Module()
@mod.action_class
class Actions:

    def hud_create_virtual_key(action: Union[str, Callable], text: str = '', icon: str = '', colour: str = '', text_colour: str = '', x: int = 0, y: int = 0, width: int = -1, height: int = -1 ) -> dict:
        """Create a virtual key to be used in a dwell toolbar or a virtual keyboard"""
        # Make sure something is visible if no text is given
        if text == '' and icon == '':
           text = '  '
           
        # If the action is a string, we default to it being a keypress
        callback = action
        if isinstance(action, str):
            callback = lambda action=action: actions.key(action)

        return {
            "callback": callback,
            "text": text,
            "icon": icon,
            "colour": colour,
            "text_colour": text_colour,
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }

    def hud_register_dwell_toolbar(name: str, virtual_keys: list, dwell_ms: int = 750, layout_style: str = 'open', alignment: str = 'left', horizontal_key_amount: int = 3, vertical_key_amount: int = 5):
        """Register a toolbar that can be activated with dwell regions"""
        global dwell_toolbar_poller
        dwell_toolbar_poller.add_toolbar(name, virtual_keys, dwell_ms, layout_style, alignment, horizontal_key_amount, vertical_key_amount)

    def hud_set_dwell_toolbar(name: str = None, monitor: int = 0, visible: Union[bool, int] = True):
        """Show the dwell toolbar screen regions"""
        global dwell_toolbar_poller
        if name is None or name == '':
            actions.user.hud_deactivate_poller("dwell_toolbar")
        else:
            actions.user.hud_activate_poller("dwell_toolbar")
            dwell_toolbar_poller.set_toolbar(name, monitor, visible)

    def hud_set_dwell_toolbar_visibility(visible: Union[bool, int] = True):
        """Set the visibility of the current dwell toolbar"""
        global dwell_toolbar_poller
        dwell_toolbar_poller.set_visibility(visible)

    def hud_activate_dwell_key():
        """Activate a toolbar item manually"""
        global dwell_toolbar_poller
        dwell_toolbar_poller.activate_cursor()

    def hud_deactivate_dwell_key():
        """Clear the currently selected toolbar item"""
        global dwell_toolbar_poller
        dwell_toolbar_poller.clear_cursor()