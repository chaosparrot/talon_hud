from talon import actions, cron, scope, Module, ui
from talon.types.point import Point2d
from talon_init import TALON_USER
from talon.scripting import Dispatch
from user.talon_hud.content.typing import HudPanelContent, HudButton, HudChoice, HudChoices, HudScreenRegion, HudAudioCue
import time
from typing import Callable, Any, Union
import os

hud_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
max_log_length = 50
mod = Module()

# Contains the state of the content inside of the head up display
# Widget data like hover states are contained within the widget
# NOTE - THIS USES A TALON API THAT IS SUBJECT TO CHANGE AND MIGHT BREAK IN FUTURE VERSIONS
class HeadUpDisplayContent(Dispatch):

    queued_log_splits = None
    throttled_logs = None

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
        "phrases": [],        
        "abilities": [],
        "walkthrough_voice_commands": [],
        "walkthrough_progress": {"current": 0, "total": 0, "progress": 0},
        "topics": {
            'debug': HudPanelContent('debug', '', 'Debug panel', [], 0, False),
        },
        "screen_regions": {
           "cursor": []
        },
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

    def register_cue(self, cue: HudAudioCue):
        self.dispatch("register_audio_cue", cue)
            
    def unregister_cue(self, cue_id):
        self.dispatch("unregister_audio_cue", cue_id)
        
    def trigger_audio_cue(self, cue_title):
        cue_id = cue_title.lower().replace(" ", "_")    
        self.dispatch("trigger_audio_cue", cue_id)        
            
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

    def append_to_phrases(self, phrase_data):
        self.content['phrases'].append(phrase_data)
        self.content['phrases'][-max_log_length:]
        self.dispatch("content_update", self.content)
        
    def append_to_log(self, type, log_message):
        self.content['log'].append({'type': type, 'message': log_message, 'time': time.monotonic()})
        self.content['log'][-max_log_length:]
        if self.queued_log_splits:
            self.revise_log(True)
        else:
            self.dispatch("log_update", self.content['log'])

    def show_throttled_logs(self, sleep_s: int = 0):
        if sleep_s:
            actions.sleep(sleep_s)
        
        if self.throttled_logs:
            for log in self.throttled_logs:
                self.content['log'].append(log)
                self.content['log'][-max_log_length:]
                if self.queued_log_splits:
                    self.revise_log(True)
                else:
                    self.dispatch("log_update", self.content['log'])
            self.throttled_logs = []

    def revise_log(self, send_update = False):
        revised_indecis = []        
        for queue_index, queued_log in enumerate(self.queued_log_splits):
            type = queued_log['type']
            prefix = queued_log['prefix']
            discard_remaining = queued_log['discard_remaining']
            throttled = queued_log['throttled']
            
            log_amount = len(self.content['log'])
            if log_amount > 0:
                
                # Get the last index of the type of log we are after
                index = -1
                log = None
                for i in range(0, log_amount):
                    if i == 0:
                       i += 1
                    
                    if self.content['log'][-i]['type'] == type:
                        index = i
                        log = self.content['log'][-i]
                        break
                
                if index != -1 and log['message'].startswith(prefix):
                    revised_indecis.append( queue_index )
                    remaining = log['message'][len(prefix):].lstrip()
                    if remaining:
                        self.content['log'][-index]['message'] = prefix.strip()
                        if send_update:
                            self.dispatch("log_update", self.content['log'])
                        
                        revised_logs = [self.content['log'][-index]]
                        if not discard_remaining:
                            remainder_log = {'type': type, 'message': remaining, 'time': log['time']}
                            
                            if not throttled:
                                revised_logs.append(remainder_log)
                                if index >= log_amount or index == 1:
                                    self.content['log'].append(remainder_log)
                                else:
                                    self.content['log'].insert(-index, remainder_log)
                            else:
                                self.throttled_logs.append(remainder_log)
                        
                        if send_update == False:
                            self.dispatch("log_revise", revised_logs)
    
        # Remove the queued splits from the log in reverse to preserve the order
        revised_indecis.reverse()
        for queue_index in revised_indecis:
            self.queued_log_splits.pop(queue_index)
    
        if send_update:
            self.dispatch("log_update", self.content['log'])                        
    
    
    def edit_log_message(self, prefix, throttled = False, discard_remaining = False, type = "command"):
        if self.queued_log_splits is None:
            self.queued_log_splits = []
        if self.throttled_logs == None:
            self.throttled_logs = []
        self.queued_log_splits.append({"type": type, "prefix": prefix, 
            "discard_remaining": discard_remaining, "throttled": throttled})
        self.revise_log()
        
hud_content = HeadUpDisplayContent()

@mod.action_class
class Actions:

    def hud_add_log(type: str, message: str):
        """Adds a log to the HUD"""
        global hud_content
        hud_content.append_to_log(type, message)
        
    def hud_edit_log(prefix_split: str, throttle_remaining: int = 0, discard_remaining: int = 0, type: str = "command"):
        """Edits a log message to be split up into multiple with optional discarding of the remainder"""
        global hud_content
        hud_content.edit_log_message(prefix_split, throttle_remaining > 0, discard_remaining > 0, type)
        
    def hud_show_throttled_logs(sleep_s: int = 0):
        """Sends the throttled log messages to be visualized after the optional sleep timeout"""
        global hud_content
        hud_content.show_throttled_logs(sleep_s)

    def hud_add_status_icon(id: str, image: str):
        """Add an icon to the status bar"""
        global hud_content
        hud_content.add_to_set("status_icons", {
            "id": id,
            "image": image,
            "explanation": "",
            "clickable": False
        })

    def hud_set_walkthrough_voice_commands(commands: list[str], progress: Any = None):
        """Set the voice commands uttered by the user during the walkthrough step"""
        global hud_content
        dict = {
            "walkthrough_said_voice_commands": commands,
        }
        if progress is not None:
            dict["walkthrough_progress"] = progress
        
        hud_content.update(dict)

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
                
    def hud_add_phrase(phrase: str, timestamp: float, time_ms: float, model: str, microphone: str):
        """Add a phrase to the phrase log"""
        global hud_content
        hud_content.append_to_phrases({
            "phrase": phrase,
            "time_ms": time_ms,
            "timestamp": timestamp,
            "model": model,
            "microphone": microphone
        })
    
    def hud_refresh_content():
        """Sends a refresh event to all the widgets where the content has changed"""
        global hud_content
        hud_content.dispatch("content_update", hud_content.content)
        
    def hud_publish_content(content: str, topic: str = '', title:str = '', show: Union[bool, int] = True, buttons: list[HudButton] = None, tags: list[str] = None):
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
        
    def hud_create_screen_region(topic: str, colour: str = None, icon: str = None, title: str = None, hover_visibility: Union[bool, int] = False, x: int = 0, y: int = 0, width: int = 0, height: int = 0, relative_x: int = 0, relative_y: int = 0):
        """Create a HUD screen region, where by default it is active all over the available space and it is visible only on a hover"""
        rect = ui.Rect(x, y, width, height) if width * height > 0 else None
        point = Point2d(x + relative_x, y + relative_y)
        return HudScreenRegion(topic, title, icon, colour, rect, point, hover_visibility)

    def hud_publish_screen_regions(type: str, regions: list[HudChoices], clear: Union[bool, int] = False):
        """Publish screen regions to widgets that can handle them, optionally clearing the type"""
        global hud_content        
        if len(regions) > 0:
            if type not in hud_content.content["screen_regions"]:
                hud_content.content["screen_regions"][type] = []        
        
            if clear:
                for region in regions:
                    actions.user.hud_clear_screen_regions(type, region.topic, False)
            
            hud_content.content["screen_regions"][type].extend(regions)
            hud_content.dispatch("content_update", hud_content.content)
        
    def hud_clear_screen_regions(type: str, topic: str = None, update: Union[bool, int] = True):
        """Clear the screen regions in the given type, optionally by topic"""
        global hud_content
        if type in hud_content.content["screen_regions"]:
            if topic is not None:
                regions = hud_content.content["screen_regions"][type]
                if len(regions) > 0:                
                    hud_content.content["screen_regions"][type] = [x for x in regions if x.topic != topic]
            else:
                hud_content.content["screen_regions"][type] = []
                
            if update:
                hud_content.dispatch("content_update", hud_content.content)

    def hud_create_choices(choices_list: list[Any], callback: Callable[[Any], None], multiple: Union[bool, int] = False) -> HudChoices:
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
        
    def hud_register_audio_cue(title: str, description: str, file: str, enabled: Union[bool, int] = True):
        """Register an audio cue which may be triggered by a poller"""
        cue_id = title.lower().replace(" ", "_")
        global hud_content        
        hud_content.register_cue(HudAudioCue(cue_id, title, description, file, 75, enabled > 0))
        
    def hud_unregister_audio_cue(title: str):
        """Register an audio cue which may be triggered by a poller"""
        cue_id = title.lower().replace(" ", "_")
        global hud_content
        hud_content.unregister_cue(cue_id)
        
    def hud_trigger_audio_cue(title: str):
        """Trigger an audio cue if it exists and if it is enabled"""
        cue_id = title.lower().replace(" ", "_")
        global hud_content
        hud_content.trigger_audio_cue(cue_id)
