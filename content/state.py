from talon import actions, Module, ui
from talon.types.point import Point2d
from talon_init import TALON_USER
from talon.scripting import Dispatch
from .typing import HudPanelContent, HudButton, HudChoice, HudChoices, HudScreenRegion, HudAudioCue, HudDynamicVoiceCommand, HudLogMessage, HudContentEvent, HudAbilityIcon, HudStatusIcon, HudStatusOption
from typing import Callable, Any, Union
import time
import os

max_log_length = 50
mod = Module()

CLAIM_BROADCAST = 0 # Broadcast to any widget that listens for this topic type
CLAIM_WIDGET = 1 # Claim a single widget and send the content towards it
CLAIM_WIDGET_TOPIC_TYPE = 2 # Claim a single widget and clear out the topic type attached to it

# Contains the state of the content inside of the head up display
# Widget data like hover states are contained within the widget
# NOTE - THIS USES A TALON API THAT IS SUBJECT TO CHANGE AND MIGHT BREAK IN FUTURE VERSIONS
class HeadUpDisplayContent(Dispatch):

    queued_log_splits = None
    throttled_logs = None
    
    topic_types = {
        "variable": {
            "mode": "command"
        },
        "log_messages": {
            "command": [],
            "error": [],
            "event": [],
            "warning": [],
            "success": [],
            "phrase": [],
            "announcer": []
        },
        "walkthrough_step": {},
        "text": {},
        "choice": {},
        "status_icons": {},
        "status_options": {},        
        "ability_icons": {},
        "cursor_regions": {},        
        "screen_regions": {},
    }
            
    # Publish content meant for text boxes and other panels
    def publish(self, topic_type, panel_content: HudPanelContent):
        if not topic_type in self.topic_types:
            self.topic_types[topic_type] = {}
        self.topic_types[topic_type][panel_content.topic] = panel_content
        self.dispatch("broadcast_update", HudContentEvent(topic_type, panel_content.topic, panel_content, "replace", CLAIM_WIDGET_TOPIC_TYPE, panel_content.show ))
    
    # Publish content directly through the event system
    def publish_event(self, topic_type, topic, data, operation, show = False, claim = 0):
        if operation == "replace":
            self.update_topic_type(topic_type, topic, data, False)
        elif operation == "remove":
            self.clear_topic_type(topic_type, topic, False)
        
        self.dispatch("broadcast_update", HudContentEvent(topic_type, topic, data, operation, claim, show))

    # Update a topic type if the content has changed
    def update_topic_type(self, topic_type, topic, data, send_event = True) -> bool:
        updated = False
        if topic_type in self.topic_types:
            if not topic in self.topic_types[topic_type]:
               self.topic_types[topic_type][topic] = None
               
            if self.topic_types[topic_type][topic] != data:
               updated = True
            self.topic_types[topic_type][topic] = data
            
            if updated and send_event:
               self.dispatch("broadcast_update", HudContentEvent(topic_type, topic, data, "replace"))
        return updated
               
    # Extend a topic type if the content has changed
    def extend_topic_type(self, topic_type, topic, data, send_event = True):
        updated = False    
    
        if topic_type in self.topic_types:
            if topic not in self.topic_types[topic_type]:
               self.topic_types[topic_type][topic] = []
            if isinstance(data, list) and len(data) > 0:
               self.topic_types[topic_type][topic].extend(data)
               updated = True
            else:
               self.topic_types[topic_type][topic].append(data)
               updated = True
            
            if updated and send_event:
                self.dispatch("broadcast_update", HudContentEvent(topic_type, topic, self.topic_types[topic_type][topic], "replace"))
		        
    # Clears a topic in a topic type if there is content
    def clear_topic_type(self, topic_type, topic, send_event=True) -> bool:
        removed = False
        if topic_type in self.topic_types:
            if topic in self.topic_types[topic_type]:
               del self.topic_types[topic_type][topic]
               removed = True
            if removed and send_event:
                self.dispatch("broadcast_update", HudContentEvent(topic_type, topic, None, "remove"))
        return removed

    def append_to_log_messages(self, topic, log_message, timestamp = None, metadata = None):    
        log_message = HudLogMessage(timestamp if timestamp else time.monotonic(), topic, log_message, metadata)
        if topic not in self.topic_types["log_messages"]:
            self.topic_types["log_messages"][topic] = []
        self.topic_types["log_messages"][topic].append(log_message)
        self.topic_types["log_messages"][topic][-max_log_length:]
        
        if self.queued_log_splits:
            self.revise_log(True)
        else:
            self.dispatch("broadcast_update", HudContentEvent("log_messages", topic, log_message, "append"))

    def show_throttled_logs(self, sleep_s: float = 0):
        if sleep_s:
            actions.sleep(sleep_s)
        
        if self.throttled_logs:
            for log_message in self.throttled_logs:
                self.topic_types["log_messages"][log_message.type].append(log_message)
                self.topic_types["log_messages"][log_message.type][-max_log_length:]
                if self.queued_log_splits:
                    self.revise_log(True)
                else:
                    self.dispatch("broadcast_update", HudContentEvent("log_messages", log_message.type, log_message, "append"))
            self.throttled_logs = []

    def revise_log(self, send_update = False):
        revised_indecis = []
        updated_logs = []
        for queue_index, queued_log in enumerate(self.queued_log_splits):
            type = queued_log["type"]
            prefix = queued_log["prefix"]
            discard_remaining = queued_log["discard_remaining"]
            throttled = queued_log["throttled"]
            
            log_amount = len(self.topic_types["log_messages"][type])
            if log_amount > 0:
                
                index = log_amount - 1
                log = self.topic_types["log_messages"][type][index] if index != -1 and index < log_amount else None
                
                if index != -1 and log is not None and log.message.startswith(prefix):
                    revised_indecis.append( queue_index )
                    remaining = log.message[len(prefix):].lstrip()
                    if remaining:
                        self.topic_types["log_messages"][type][index].message = prefix.strip()
                               
                        revised_logs = [self.topic_types["log_messages"][type][index]]
                        if not discard_remaining:
                            remainder_log = HudLogMessage(log.time, type, remaining)
                            
                            if not throttled:
                                revised_logs.append(remainder_log)
                                if index >= log_amount or index == 1:
                                    self.topic_types["log_messages"][type].append(remainder_log)
                                else:
                                    self.topic_types["log_messages"][type].insert(index, remainder_log)
                            else:
                                self.throttled_logs.append(remainder_log)
                        
                        if send_update == False:
                            event = HudContentEvent("log_messages", type, revised_logs, "patch")
                            self.dispatch("broadcast_update", event)
    
        # Remove the queued splits from the log in reverse to preserve the order
        revised_indecis.reverse()
        for queue_index in revised_indecis:
            self.queued_log_splits.pop(queue_index)
        
        if send_update and len(updated_logs):
            self.dispatch("broadcast_update", HudContentEvent("log_messages", type, updated_logs, "patch"))
    
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
        hud_content.append_to_log_messages(type, message)
        
    def hud_edit_log(prefix_split: str, throttle_remaining: int = 0, discard_remaining: int = 0, type: str = "command"):
        """Edits a log message to be split up into multiple with optional discarding of the remainder"""
        global hud_content
        hud_content.edit_log_message(prefix_split, throttle_remaining > 0, discard_remaining > 0, type)
        
    def hud_show_throttled_logs(sleep_s: int = 0):
        """Sends the throttled log messages to be visualized after the optional sleep timeout"""
        global hud_content
        hud_content.show_throttled_logs(sleep_s)

    def hud_add_status_icon(id: str, image: str):
        """Add an unclickable icon to the status bar"""
        global hud_content
        status_icon = HudStatusIcon(id, image)
        hud_content.update_topic_type("status_icons", id, status_icon)
        
    def hud_publish_status_icon(topic: str, icon: HudStatusIcon):
        """Publish an icon the status bar"""
        global hud_content
        hud_content.update_topic_type("status_icons", topic, status_icon)
        
    def hud_remove_status_icon(id: str):
        """Remove an icon to the status bar"""
        global hud_content
        hud_content.clear_topic_type("status_icons", id)
        
    def hud_publish_status_option(topic: str, status_option: HudStatusOption):
        """Add an option entry to the status bar"""
        global hud_content
        hud_content.update_topic_type("status_options", topic, status_option)
        
    def hud_remove_status_option(topic: str):
        """Remove an option entry to the status bar"""
        global hud_content
        hud_content.clear_topic_type("status_options", topic)

    def hud_add_ability(id: str, image: str, colour: str, enabled: int, activated: int, image_offset_x: int = 0, image_offset_y: int = 0):
        """Add a hud ability or update it"""
        global hud_content        
        ability_icon = HudAbilityIcon(image, colour, enabled > 0, 5 if activated > 0 else 0, image_offset_x, image_offset_y)
        hud_content.update_topic_type("ability_icons", id, ability_icon)
        
    def hud_remove_ability(id: str):
        """Remove an ability"""
        global hud_content
        hud_content.clear_topic_type("ability_icons", id)

    def hud_publish_content(content: str, topic: str = "", title:str = "", show: Union[bool, int] = True, buttons: list[HudButton] = None, voice_commands: Any = None):
        """Publish a specific piece of content to a topic"""            
        if buttons == None:
            buttons = []
            
        commands = []
        if voice_commands == None:
            commands = {}
        else:
            for voice_command in voice_commands:
                commands.append(HudDynamicVoiceCommand(voice_command, voice_commands[voice_command]))
            
        content = HudPanelContent(topic, title, [content], buttons, time.time(), show, voice_commands=commands)
        
        global hud_content
        hud_content.publish("text", content)
        
    def hud_create_button(text: str, callback: Callable[[], None], image: str = ""):
        """Create a button used in the Talon HUD"""
        return HudButton(image, text, ui.Rect(0,0,0,0), callback)
        
    def hud_create_status_option(icon_topic: str, default_option: HudButton, activated_option: HudButton):
        """Create an option entry to show in the options in the status bar"""
        return HudStatusOption(icon_topic, default_option, activated_option)
        
    def hud_create_screen_region(topic: str, colour: str = None, icon: str = None, title: str = None, hover_visibility: Union[bool, int] = False, x: int = 0, y: int = 0, width: int = 0, height: int = 0, relative_x: int = 0, relative_y: int = 0):
        """Create a HUD screen region, where by default it is active all over the available space and it is visible only on a hover"""
        rect = ui.Rect(x, y, width, height) if width * height > 0 else None
        point = Point2d(x + relative_x, y + relative_y)
        return HudScreenRegion(topic, title, icon, colour, rect, point, hover_visibility)

    def hud_publish_screen_regions(type: str, regions: list[HudScreenRegion], clear: Union[bool, int] = False):
        """Publish screen regions to widgets that can handle them, optionally clearing the type"""
        global hud_content
        if len(regions) > 0:
            screen_region_type = "cursor_regions" if type == "cursor" else "screen_regions"
            region_by_topic = {}
            for region in regions:
                if region.topic not in region_by_topic:
                    region_by_topic[region.topic] = []
                region_by_topic[region.topic].append(region)            
            
            if clear:
                for region_topic in region_by_topic:
                    hud_content.clear_topic_type(screen_region_type, region_topic, False)
            
            for region_topic in region_by_topic:
                hud_content.extend_topic_type(screen_region_type, region_topic, regions)

    def hud_clear_screen_regions(type: str, topic: str = None, _deprecated_update: Union[bool, int] = True):
        """Clear the screen regions in the given type, optionally by topic"""
        global hud_content
        screen_region_type = "cursor_regions" if type == "cursor" else "screen_regions"
        hud_content.clear_topic_type(screen_region_type, topic)

    def hud_create_choices(choices_list: list[Any], callback: Callable[[Any], None], multiple: Union[bool, int] = False) -> HudChoices:
        """Creates a list of choices with a single list of dictionaries"""
        choices = []
        for index, choice_data in enumerate(choices_list):
            image = choice_data["image"] if "image" in choice_data else ""
            choices.append(HudChoice(image, choice_data["text"], choice_data, "selected" in choice_data and choice_data["selected"], ui.Rect(0,0,0,0)))
        return HudChoices(choices, callback, multiple)
        
    def hud_publish_choices(choices: HudChoices, title: str = "", content:str = ""):
        """Publish choices to a choice panel"""
        if title == "":
            title = "Choices"
        if content == "":
            content = "Pick any from the following choices using <*option <number>/>"
        
        content = HudPanelContent("choice", title, [content], [], time.time(), True, choices)
        global hud_content
        hud_content.publish("choice", content)