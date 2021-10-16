from talon import actions, cron, scope, Module, ui
from talon_init import TALON_USER
from talon.scripting import Dispatch
from user.talon_hud.content.typing import HudPanelContent, HudButton, HudChoice, HudChoices
import time
from typing import Callable, Any
import os

hud_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        "walkthrough_voice_commands": [],
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

    def hud_set_walkthrough_voice_commands(commands: list[str]):
        """Set the voice commands uttered by the user during the walkthrough step"""
        global hud_content
        hud_content.update({"walkthrough_said_voice_commands": commands})

    def hud_remove_status_icon(id: str):
        """Remove an icon to the status bar"""
        global hud_content
        hud_content.remove_from_set("status_icons", {
            "id": id
        })

    def hud_add_ability(id: str, image: str, colour: str, enabled: int, activated: int, image_offset_x: int = 0, image_offset_y: int = 0):
        """Add a hud ability or update it"""
        global hud_content
        hud_content.add_to_set("abilities", {
            "id": id,
            "image": image,
            "colour": colour,
            "enabled": enabled > 0,
            "activated": 5 if activated > 0 else 0,
            "image_offset_x": image_offset_x,
            "image_offset_y": image_offset_y
        })

    def hud_remove_ability(id: str):
        """Remove an ability"""
        global hud_content
        hud_content.remove_from_set("abilities", {
            "id": id
        })
        
    def hud_refresh_content():
        """Sends a refresh event to all the widgets where the content has changed"""
        global hud_content
        hud_content.dispatch("content_update", hud_content.content)
        
    def hud_publish_content(content: str, topic: str = '', title:str = '', show:bool = True, buttons: list[HudButton] = None, tags: list[str] = None):
        """Publish a specific piece of content to a topic"""            
        if buttons == None:
            buttons = []
        if tags == None:
            tags = []
        content = HudPanelContent(topic, title, [content], buttons, time.time(), show, tags = tags)
        
        global hud_content
        hud_content.publish(content)
        
    def hud_create_button(text: str, callback: Callable[[], None], image: str = ''):
        """Create a button used in the Talon HUD"""
        return HudButton(image, text, ui.Rect(0,0,0,0), callback)

    def hud_create_choices(choices_list: list[Any], callback: Callable[[Any], None], multiple: bool = False) -> HudChoices:
        """Creates a list of choices with a single list of dictionaries"""
        choices = []
        for index, choice_data in enumerate(choices_list):
            image = choice_data['image'] if 'image' in choice_data else ''
            choices.append(HudChoice(image, choice_data['text'], choice_data, "selected" in choice_data and choice_data["selected"], ui.Rect(0,0,0,0)))
        return HudChoices(choices, callback, multiple)
        
    def hud_publish_choices(choices: HudChoices, title: str = '', content:str = ''):
        """Publish choices to a choice panel"""
        if title == "":
            title = "Choices"
        if content == "":
            content = "Pick any from the following choices using <*option <number>/>"
        
        content = HudPanelContent("choice", title, [content], [], time.time(), True, choices)
        global hud_content
        hud_content.publish(content)
                
    def show_test_choices():
        """Show a bunch of test buttons to choose from"""
        choices = actions.user.hud_create_choices([{"text": "Testing", "image": "next_icon"},{"text": "Another choice"},{"text": "Some other choice"},{"text": "Maybe pick this"},], print)
        actions.user.hud_publish_choices(choices)
