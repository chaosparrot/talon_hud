from talon import actions, cron, scope, Module, ui
from talon.scripting import Dispatch
from user.talon_hud.content.typing import HudPanelContent, HudButton, HudChoice, HudChoices
import time
from typing import Callable, Any

max_log_length = 50
mod = Module()

# Contains the state of the content inside of the head up display
# Widget data like hover states are contained within the widget
# NOTE - THIS USES A TALON API THAT IS SUBJECT TO CHANGE AND MIGHT BREAK IN FUTURE VERSIONS
class HeadUpDisplayContent(Dispatch):

    # Default content to be displayed
    content = {
        'mode': 'command',
        'language': 'en_US',
        'programming_language': {
            'ext': '',
            'forced': False
        },
        "status_icons": [],
        "log": [],
        "abilities": [],
        "topics": {
            'debug': HudPanelContent('debug', '', 'Debug panel', [], 0, False),
        }
    }
    
    # Publish content meant for text boxes and other panels
    def publish(self, panel_content: HudPanelContent):
        topic = panel_content.topic

        self.content['topics'][topic] = panel_content
        self.dispatch('panel_update', panel_content)
    
    # Update the content and sends an event if the state has changed
    def update(self, dict):
        updated = False
        for key in dict:
            if (key in self.content):
                if not updated and self.content[key] != dict[key]:
                    updated = True
                self.content[key] = dict[key]
            
            if (key not in self.content):
                updated = True
                self.content[key] = dict[key]
        
        if updated:
            self.dispatch("content_update", self.content)
            
            
    # Update a specific list in the content and make sure they are unique
    def add_to_set(self, content_key, dict):
        updated = False        
        if content_key in self.content and isinstance(self.content[content_key], list):
            found = False
            for index, item in enumerate(self.content[content_key]):
                if item['id'] == dict['id']:
                    found = True
                    updated = item != dict
                    self.content[content_key][index] = dict
                    break
            
            if not found:
                updated = True
                self.content[content_key].append(dict)
        
        if updated:
            self.dispatch("content_update", self.content)

    # Removes a key in the set of content
    def remove_from_set(self, content_key, dict):
        updated = False        
        if content_key in self.content and isinstance(self.content[content_key], list):
            new_set = list(filter(lambda item, item_to_remove=dict: item['id'] != item_to_remove['id'], self.content[content_key]))
            if len(new_set) != len(self.content[content_key]):
                updated = True
                self.content[content_key] = new_set
        
        if updated:
            self.dispatch("content_update", self.content)
        
    def append_to_log(self, type, log_message):
        self.content['log'].append({'type': type, 'message': log_message, 'time': time.monotonic()})
        self.content['log'][-max_log_length:]
        self.dispatch("log_update", self.content['log'])
        
hud_content = HeadUpDisplayContent()

documentation = """
By default, the widgets except for the status bar will hide when Talon goes in sleep mode, but you can keep them around, or hide them, with the following commands.  
<*head up show <widget name> on sleep/> keeps the chosen widget enabled during sleep mode.  
<*head up hide <widget name> on sleep/> hides the chosen widget when sleep mode is turned on.

On top of being able to turn widgets on and off, you can configure their attributes to your liking.  
Currently, you can change the size, position, alignment, animation and font size.  

<*head up drag <widget name>/> starts dragging the widget.  
<*head up resize <widget name>/> starts resizing the widgets width and height.  
<*head up expand <widget name>/> changes the maximum size of the widget in case the content does not fit the regular width and height.  
By default these two dimensions are the same so the widget does not grow when more content is added.  
<*head up text scale <widget name>/> starts resizing the text in the widget.  
<*head up drop/> confirms and saves the changes of your changed widgets.  
<*head up cancel/> cancels the changes. Hiding a widget also discards of the current changes.

Some widgets like the event log also allow you to change the text direction and alignment  
<*head up align <widget name> left/> aligns the text and the widget to the left side of its bounds.  
<*head up align <widget name> right/> aligns the text and the widget to the right side of its bounds.  
<*head up align <widget name> top/> changes the direction in which content is placed upwards.  
<*head up align <widget name> bottom/> changes the direction in which content is placed downwards.

If you prefer having a more basic animation free set up, or want to switch back to an animated display, you can use the following commands  
<*head up basic <widget name>/> disables animations on the chosen widget.  
<*head up fancy <widget name>/> enables animations on the chosen widget.
"""

@mod.action_class
class Actions:

    def hud_add_log(type: str, message: str):
        """Adds a log to the HUD"""
        global hud_content
        hud_content.append_to_log(type, message)

    def hud_add_status_icon(id: str, image: str):
        """Add an icon to the status bar"""
        global hud_content
        hud_content.add_to_set("status_icons", {
            "id": id,
            "image": image,
            "explanation": "",
            "clickable": False
        })

    def hud_remove_status_icon(id: str):
        """Remove an icon to the status bar"""
        global hud_content
        hud_content.remove_from_set("status_icons", {
            "id": id
        })

    def add_hud_ability(id: str, image: str, colour: str, enabled: bool, activated: bool):
        """Add a hud ability or update it"""
        global hud_content
        hud_content.add_to_set("abilities", {
            "id": id,
            "image": image,
            "colour": colour,
            "enabled": enabled,
            "activated": 5 if activated else 0
        })

    def remove_hud_ability(id: str):
        """Remove an ability"""
        global hud_content
        hud_content.remove_from_set("abilities", {
            "id": id
        })
        
    def hud_publish_content(content: str, topic: str = '', title:str = '', show:bool = True, buttons: list[HudButton] = None):
        """Publish a specific piece of content to a topic"""            
        if buttons == None:
            buttons = []
        content = HudPanelContent(topic, title, [content], buttons, time.time(), show)
        
        global hud_content
        hud_content.publish(content)
        
    def hud_create_button(text: str, callback: Callable[[], None], image: str = ''):
        """Create a button used in the Talon HUD"""
        return HudButton(image, text, ui.Rect(0,0,0,0), callback)

    def hud_create_choices(choices_list: list[Any], selected_indexes: list[int]):
        """Creates a list of choices with a single list of dictionaries"""
        choices = []
        for index, choice_data in enumerate(choices_list):
            image = choice_data['image'] if 'image' in choice_data else 'check_icon' if index in selected_indexes else ''
            choices.append(HudChoice(image, choice_data['text'], choice_data, index in selected_indexes, ui.Rect(0,0,0,0)))
        return choices
        
    def hud_get_documentation():
        """Publish a specific piece of content to a topic"""
        content = HudPanelContent("documentation", "Head up documentation", [documentation], [], time.time(), True)
        
        global hud_content
        hud_content.publish(content)
        
        
    def show_test_choices():
        """Show a bunch of test buttons to choose from"""
        choices = actions.user.hud_create_choices([{"text": "Testing"},{"text": "Another choice"},{"text": "Some other choice"},{"text": "Maybe pick this"},], [])
        choiceContent = HudChoices(choices, print)
        content = HudPanelContent("choice", "Choices", ["Pick any from the following choices using <*option <number>/>"], [], time.time(), True, choiceContent)
        
        global hud_content
        hud_content.publish(content)        
