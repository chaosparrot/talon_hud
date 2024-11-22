from typing import Dict
from talon import ui, actions, app, canvas, cron
from .utils import string_to_speakable_string
from .content.typing import HudAccessibleNode

class HeadUpFocusManager:
    
    # Control scheme
    # https://w3c.github.io/aria-practices/#tabpanel
    # The HUD widget list is presented like a dynamic tab bar with interactive widgets in them
    # Pressing tab / shift-tab moves the focus inside of the widget
    # Pressing space or enter activates or selects a focused item
    # Some widgets have arrow key navigation enabled ( for next / prevous page, or selecting items )
    # Alt-tab moves the focus out of the HUD entirely
    # ESC moves the focus to the widget list, pressing it again moves the focus out of the HUD again
    focused = False
    focused_path = None    
    focused_widget_id = None
    focused_widget_item = None
    widget = None
    widget_manager = None
    event_dispatch = None
    last_focused_app = None
    focus_canvas = None
    
    accessible_root = None
    
    # Whether or not the context menu is opened first
    # Because in that case a dismissal needs to return focus to the previous application
    only_context_opened = False
    
    container_roles = ["context_menu", "menu", "radiogroup", "combobox"]
    
    def __init__(self, widget_manager, event_dispatch):
        self.accessible_root = HudAccessibleNode("Head up display", "window", path="")
        self.widget_manager = widget_manager
        self.event_dispatch = event_dispatch
        self.event_dispatch.register("hud_focused", self.focus_path)
        self.focus_canvas = canvas.Canvas(-2, -2, 1, 1)
        self.focus_canvas.blocks_mouse = True
        self.focus_canvas.register("focus", self.on_hud_focus_change)
        self.focus_canvas.register("key", self.handle_key_controls)
        self.focus_canvas.freeze()
        self.focused_nodes = []
    
    def destroy(self):
        self.accessible_root.clear()
        self.accessible_root = None
        self.focused_nodes = None        
        self.event_dispatch.unregister("hud_focused", self.focus_path)        
        self.event_dispatch = None
        self.widget = None
        self.widget_manager = None
        self.last_focused_app = None
        self.focus_canvas = canvas.Canvas(-2, -2, 1, 1)
        self.focus_canvas.unregister("focus", self.on_hud_focus_change)
        self.focus_canvas.unregister("key", self.handle_key_controls)
    
    def init_widgets(self):
        self.accessible_root.clear()
        for widget in self.widget_manager.widgets:
            if widget.id != "context_menu":
                self.accessible_root.append(HudAccessibleNode(widget.id, "widget", path=widget.id))
                widget.set_accessible_root(self.accessible_root.nodes[-1])
    
    def set_last_focused_app(self, app):
        if app.name != "Talon":
            self.last_focused_app = app

    def on_hud_focus_change(self, focused):
        if self.focused != focused:
            self.focused = focused
        
        if not focused:
            if self.focused_widget_item is not None and self.focused_widget_item.role in ["context_button", "context_menu"]:
                self.event_dispatch.hide_context_menu()

            self.focus_widget_id = None
            self.focused_widget_item = None
            if self.widget:
                self.widget.blur()
                self.widget = None
                
            if self.only_context_opened:
                self.blur()

    # Focus paths are built with dot and colon separators
    # Where the dots represent the level of a node, and the number behind the colon represents the numeral position in the list
    # widget_id:0.node:0.child_node:1
    def focus_path(self, path: str = None):
        if path is None:
            fallback = not self.focused_path
            if self.focused_path:
                path = self.focused_path
                widget_id = self.focused_widget_id if path is None else path.split(".")[0].split(':')[0]
                for widget in self.widget_manager.widgets:
                    if widget.id and not widget.enabled:
                        fallback = True
                        break
            
            # Fallback to first widget if the path no longer exist or doesn't exist
            if fallback:
                for widget in self.widget_manager.widgets:
                    if widget.enabled and widget.accessible_tree:
                        path = widget.accessible_tree.path
                        break
        
        # Make sure we do not get recursive focusing of the same path
        if self.focused_path != path or not self.focused:
            self.focused_path = path
        else:
            return
        
        #self.print_tree(self.accessible_root)
        
        widget_id = self.focused_widget_id if path is None else path.split(".")[0].split(':')[0]
        currently_in_context = self.focused_widget_item is not None and self.focused_widget_item.role in ["context_button", "context_menu"]
        self.focus(widget_id, path)
        after_in_context = self.focused_widget_item is not None and self.focused_widget_item.role in ["context_button", "context_menu"]

        message = string_to_speakable_string(self.widget.id if self.widget else "") if not self.focused_widget_item else string_to_speakable_string(self.focused_widget_item.name)
        if not self.focused:        
            message = "Head up display " + string_to_speakable_string(self.widget.id if self.widget else "")
            if self.focused_widget_item and self.focused_widget_item.role != "widget":
                message += " " + string_to_speakable_string(self.focused_widget_item.name)
            
            self.focus_canvas.freeze()
            self.focus_canvas.show()
            self.set_last_focused_app(ui.active_app())
            self.focused = True
            self.focus_canvas.focused = True
            self.only_context_opened = self.focused_widget_item is not None and self.focused_widget_item.role == "context_menu"
            
        actions.user.hud_add_log("narrate", message)

        if after_in_context:
            for possible_context_widget in self.widget_manager.widgets:
                if possible_context_widget.id == "context_menu":
                    possible_context_widget.current_focus = self.focused_widget_item
                    if currently_in_context:
                        possible_context_widget.redraw_focus()

        # Determine whether or not we need to show or hide the context menu on focus
        if currently_in_context != after_in_context:
            if not after_in_context:
                self.event_dispatch.hide_context_menu()
                self.only_context_opened = False
            else:
                self.event_dispatch.show_context_menu(self.widget.id, None, self.widget.buttons)                        

    def focus(self, widget_id: str = None, path: str = None):
        # Focus the first widget enabled if no widget is given
        widget_id = self.focused_widget_id if widget_id is None else widget_id
        if widget_id is None:
            for widget in self.widget_manager.widgets:
                if widget.enabled:
                    widget_id = widget.id
                    break
    
        if widget_id is not None:
            for widget in self.widget_manager.widgets:
                if widget.enabled and widget.id == widget_id:
                    if self.widget and self.widget.id != widget_id:
                        self.widget.blur()
                    self.widget = widget
                    self.focused_widget_id = widget.id
                    self.focused_widget_item = widget.focus(path)
                    self.focused_path = self.focused_widget_item.path if self.focused_widget_item else widget.accessible_tree.path
                    break

    def focus_up(self, item = None):
        if item is None:
            item = self.focused_widget_item
        if item is not None and item.path is not None:
            if item.role == "widget" or ( item.role in ["context_menu", "context_button"] and self.only_context_opened ):
                self.blur(False)
                return
        
            upper_path = ".".join(item.path.split(".")[:-1])
            upper_item = self.accessible_root.find( upper_path )
            if upper_item is not None and upper_item.role in self.container_roles:
                return self.focus_up(upper_item)
            elif upper_item is not None:
                self.focus_path(upper_item.path)

    def focus_next(self, path: str = None):
        """Select next focusable item"""
        self.focus_direction(path, "next")

    def focus_previous(self, path: str = None):
        """Select previous focusable item"""
        self.focus_direction(path, "previous")

    def focus_direction(self, path: str = None, direction: str = "next"):
        if self.focused_widget_item is not None:
            item = None
            focused_item = self.focused_widget_item
            initial_path = path
            if path is None:
                path = self.focused_widget_item.path
            else:
                focused_item = self.accessible_root.find(path)
            
            if focused_item.role == "widget" or ( focused_item.role == "context_menu" and initial_path is None ):
                item = focused_item.nodes[0 if direction == "next" else -1]
            else:
                # TODO FIGURE OUT RADIO ITEMS
                item_number = int(path.split(":")[-1])
                upper_path = ".".join(path.split(".")[:-1])
                upper_node = self.accessible_root.find(upper_path)
                
                # For radio and checkbox items - Skip over them with tab and only allow arrow key movement
                if focused_item.role in ["radio", "checkbox"]:
                    item_number = int(upper_path.split(":")[-1])                
                    upper_path = ".".join(upper_path.split(".")[:-1])
                    upper_node = self.accessible_root.find(upper_path)
                    
                # If the item does not exist - Skip to the item that took its place in the tab hierarchy
                if self.accessible_root.find(path) is None and direction == "next":
                    item_number -= 1
                
                if upper_node is not None:
                    if direction == "next" and item_number + 1 < len(upper_node.nodes):
                        item = upper_node.nodes[item_number + 1]
                    elif direction == "previous" and item_number - 1 >= 0:
                        item = upper_node.nodes[item_number - 1]
                    else:
                        if upper_node.role == "widget":
                            self.focus_path(upper_path)
                        else:
                            self.focus_direction(upper_path, direction)
                        return
                # TODO if parent no longer exists - Move back one parent
                else:
                    while upper_node is None and "." in upper_path:
                        parent_number = int(upper_path.split(":")[-1])
                        upper_path = ".".join(upper_path.split(".")[:-1])
                        upper_node = self.accessible_root.find(upper_path)
		            
                    if upper_node is not None:
                        if direction == "next":
                            parent_number -= 1
                        if direction == "next" and parent_number + 1 < len(upper_node.nodes):
                            item = upper_node.nodes[parent_number + 1]
                        elif direction == "previous" and parent_number - 1 >= 0:
                            item = upper_node.nodes[parent_number - 1]
                        else:
                            if upper_node.role == "widget":
                                self.focus_path(upper_path)
                            else:
                                self.focus_direction(upper_path, direction)
                            return

            while item and item.role in self.container_roles and item.nodes and len(item.nodes) > 0:
                item = item.nodes[0 if direction == "next" else -1]
           
            if item:
                self.focus_path(item.path)

    def blur(self, keep_path = True):
        if self.focused:
            self.focused = False
            self.only_context_opened = False
            
            if self.widget:
                self.widget.blur()
            
            if self.focused_widget_item and self.focused_widget_item.role in ["context_button", "context_menu"]:
                self.event_dispatch.hide_context_menu()

            if not keep_path:
                self.focused_path = None
                self.focused_widget_item = None

            if self.focus_canvas:
                self.focus_canvas.focused = False

            # Attempt to focus last app if it still exists
            if self.last_focused_app is not None:
                apps = ui.apps()
                for available_app in apps:
                    if available_app.pid == self.last_focused_app.pid:
                        self.last_focused_app.focus()
                        return

            # Do a crude alt-tab to switch the focus back to the previous window to make sure the HUD does not stay focused perpetually                  
            if app.platform == "windows":
                actions.key("alt-tab")
            elif app.platform == "linux":
                actions.key("alt-tab")
            # TODO test on macos to see if this method works
            else:
                actions.key("cmd-tab")

    def handle_key_controls(self, evt) -> bool:
        key_string = evt.key.lower() if evt.key is not None else ""
        for mod in evt.mods:    
            key_string = mod.lower() + "-" + key_string
        
        new_focus = False
        handled = True
        if key_string == "escape":
            if evt.down:
                self.focus_up()
        elif key_string == "tab" or key_string == "shift-tab":
            if evt.down:
                if key_string == "shift-tab":
                    self.focus_previous()
                else:
                    self.focus_next()
        elif key_string == "left" and ( self.focused_widget_item is None or self.focused_widget_item.role == "widget" ):
            if evt.down:
                previous_widget = None
                for widget in self.widget_manager.widgets:
                    if widget.id != self.widget.id and widget.enabled and widget.id != "context_menu":
                        previous_widget = widget
                    elif widget.id == self.widget.id:
                        break
            
                if previous_widget is not None:
                    self.widget.blur()
                    if previous_widget.accessible_tree and previous_widget.accessible_tree.path:
                        self.focus_path(previous_widget.accessible_tree.path)
        # Focus next widget if available
        elif key_string == "right" and ( self.focused_widget_item is None or self.focused_widget_item.role == "widget" ):
            if evt.down:
                widget_seen = False
                next_widget = None
                for widget in self.widget_manager.widgets:
                    if widget.id == self.widget.id:
                        widget_seen = True
                    elif widget_seen and widget.enabled and widget.id != self.widget.id and widget.id != "context_menu":
                        next_widget = widget
                        break
            
                if next_widget is not None:
                    self.widget.blur()
                    if next_widget.accessible_tree and next_widget.accessible_tree.path:
                        self.focus_path(next_widget.accessible_tree.path)
        elif ( key_string == "space" and self.focused_widget_item is not None ) or \
            ( key_string == "return" and self.focused_widget_item is not None and self.focused_widget_item.role in ["button", "context_button"]):
            if evt.down:
                self.event_dispatch.detect_autofocus()
                activated = self.widget.activate(self.focused_widget_item)
                if activated == False:
                    # If the widget could not activate the button, it might be the close button so check for that
                    if self.focused_widget_item.role == "context_button" and self.focused_widget_item.equals("closewidget"):
                        self.widget.disable(True)
                        self.event_dispatch.hide_context_menu()
                        self.blur()
                    
                # Close context menu after activating button
                elif activated and self.focused_widget_item.role == "context_button":
                        self.event_dispatch.hide_context_menu()
                        self.focused_widget_id = None                    
                        if self.widget.enabled:
                            self.widget.focus(None)
                        if self.only_context_opened:
                            self.blur()
                        
        elif self.focused_widget_item is not None and self.focused_widget_item.role in ["context_button", "context_menu"] and key_string in ["up", "down"]:
            if evt.down:
                next_index = 0
                context_menu = self.focused_widget_item
                if self.focused_widget_item.role == "context_button":
                    item_index = int(self.focused_widget_item.path.split(":")[-1])
                    next_index = item_index + 1 if key_string == "down" else item_index - 1
                    context_menu = self.accessible_root.find(".".join(self.focused_widget_item.path.split(".")[:-1]))
                else:
                    next_index = 0 if key_string == "down" else len(self.focused_widget_item.nodes ) - 1
                
                if context_menu:
                    if next_index >= 0 or next_index < len(context_menu.nodes):
                        self.focus_path(context_menu.nodes[next_index].path)
        else:
            handled = self.widget.on_key(evt) if self.widget else False
            
        # If the widget is suddenly no longer enabled after activation - Give the focus switching about 100 ms to switch to a new focus if a topic is published
        # Otherwise just blur the focus
        if handled and self.widget and not self.widget.enabled:
            current_path = self.focused_widget_item.path
            cron.after("100ms", lambda self=self, current_path=current_path: self.blur() if self.focused_widget_item is not None and self.focused_widget_item.path == current_path else "")

        return handled
        
    def print_tree(self, node: HudAccessibleNode, prefix="- "):
        print( prefix + node.path + " ( " + node.role + " )" )
        for child_node in node.nodes:
            self.print_tree(child_node, prefix + "  ")
