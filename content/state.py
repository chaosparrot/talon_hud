from talon import actions, cron, scope, Module
from talon.scripting import Dispatch
from user.talon_hud.content.typing import HudPanelContent, HudButton
import time

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
        "panel_content": {
            'debug': HudPanelContent('debug', '', 'Debug panel', [], 0, True),
            'history': HudPanelContent('history', '', 'History panel', [], 0, True),
            'choice': HudPanelContent('choice', '', 'Choice panel', [], 0, True),
            'documentation': HudPanelContent('documentation', '', 'Documentation panel', [], 0, True)
        }
    }
    
    # Publish content meant for text boxes and other panels
    def publish(self, panel_content: HudPanelContent):
        purpose = panel_content.purpose
        if purpose not in ['debug', 'history', 'choice', 'documentation']:
            purpose = 'debug'
    
        self.content['panel_content'][purpose] = panel_content
        self.dispatch('panel_update', self.content['panel_content'])
    
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
            print( dict, updated )                
        
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

    def add_hud_log(type: str, message: str):
        """Adds a log to the HUD"""
        global hud_content
        hud_content.append_to_log(type, message)

    def add_status_icon(id: str, image: str, explanation: str):
        """Add an icon to the status bar"""
        global hud_content
        hud_content.add_to_set("status_icons", {
            "id": id,
            "image": image,
            "explanation": "",
            "clickable": False
        })

    def remove_status_icon(id: str):
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
        
    def hud_publish_content(content: str, widget_hint: str = '', title:str = '', show:bool = True, buttons: list[HudButton] = None):
        """Publish a specific piece of content to a user defined widget"""            
        if buttons == None:
            buttons = []
        content = HudPanelContent(widget_hint, title, [content], buttons, time.time(), show)
        
        global hud_content
        hud_content.publish(content)