from typing import Dict
from talon import ui

class HeadUpFocusManager:
    
    # Control scheme
    # https://w3c.github.io/aria-practices/#tabpanel
    # The HUD widget list is presented like a dynamic tab bar with interactive widgets in them
    # Pressing tab / shift-tab moves the focus inside of the widget
    # Pressing space or enter activates or selects a focused item
    # Some widgets have arrow key navigation enabled ( for next / prevous page, or selecting items )
    # Alt-tab moves the focus out of the HUD entirely
    # ESC moves the focus to the widget list, pressing it again moves the focus out of the HUD again
    # If a key is not handled, it should leak through to the focused window
    focused_widget_id = None
    focused_widget_item = None
    widget = None
    widget_manager = None
    
    def __init__(self, widget_manager):
        self.widget_manager = widget_manager
        
    # Set focus registers on widgets
    def set_focus_events(self):
        for widget in self.widget_manager.widgets:
            widget.set_focus_events(self.on_focus, self.on_blur, self.handle_base_focus_controls)
    
    def on_focus(self, focused_widget = None):
        focusable_widgets = []
        widget_to_focus_id = focused_widget.id if focused_widget else self.focused_widget_id
        for widget in self.widget_manager.widgets:
            if widget.enabled:
                focusable_widgets.append(widget)
            if widget.enabled and widget.id != "context_menu" and ( widget.id == widget_to_focus_id or self.focused_widget_id == None ):
                self.widget = widget
                self.focused_widget_id = widget.id
                self.widget.focus(self.focused_widget_item)
                return
        
        # If no widget was focused, retry by focusing the first enabled widget
        if len(focusable_widgets) > 0:
            self.on_focus(focusable_widgets[0])

    def on_blur(self):
        if self.widget:
            self.widget.blur()

    def handle_base_focus_controls(self, evt) -> bool:
        key_string = evt.key
        for mod in evt.mods: 
            key_string = mod + "-" + key_string
        handled = True
        if key_string == "alt-tab":
            if self.widget != None and evt.event == "keydown":
                self.widget.blur()
        elif key_string == "esc":
            if focused_widget_item == None and evt.event == "keydown":
                if self.widget != None:
                    self.widget.blur()
            elif self.widget:
                self.focused_widget_item = self.widget.focus_up()
        elif key_string == "tab" and self.widget:
            if evt.event == "keydown":
                self.focused_widget_item = self.widget.focus_next()
        elif key_string == "shift-tab" and self.widget:
            if evt.event == "keydown":
                self.focused_widget_item = self.widget.focus_previous()
        elif key_string == "left" and self.focused_widget_item == None:
            if evt.event == "keydown":
                previous_widget = None
                for widget in self.widget_manager.widgets:
                    if widget.id != self.widget.id and widget.enabled and widget.id != "context_menu":
                        previous_widget = widget
                    elif widget.id == self.widget.id:
                        break
            
                if previous_widget is not None:
                    self.widget.blur()
                    self.widget = previous_widget
                    self.focused_widget_id = self.widget.id
                    print( self.focused_widget_id )                    
                    self.focused_widget_item = self.widget.focus()
                else:
                    print( "NO PREVIOUS WIDGET - SOUND ERROR" )
        # Focus next widget if available
        elif key_string == "right" and self.focused_widget_item == None:
            if evt.event == "keydown":        
                widget_seen = False
                next_widget = None
                for widget in self.widget_manager.widgets:
                    if widget.id == self.widget.id:
                        widget_seen = True
                    elif widget_seen and widget.enabled and widget.id != self.widget.id and widget.id != "context_menu":
                        next_widget = widget
            
                if next_widget is not None:
                    self.widget.blur()
                    self.widget = next_widget
                    self.focused_widget_id = self.widget.id
                    print( self.focused_widget_id )
                    self.focused_widget_item = self.widget.focus()
                else:
                    print( "NO NEXT WIDGET - SOUND ERROR" )
        elif key_string == "space" and self.focused_widget_item is not None:
            if evt.event == "keydown":
                self.widget.activate_focus()
        else:
            handled = False
            
        return handled