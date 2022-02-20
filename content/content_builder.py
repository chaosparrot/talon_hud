from .state import HeadUpDisplayContent
from .typing import *
from typing import Union, Any, Callable
from ..utils import retrieve_available_voice_commands
import time

# Class for managing a part of the HUD content
class HudContentBuilder():
    _content: HeadUpDisplayContent = None

    def __init__(self, content: HeadUpDisplayContent):
        self.connect(content)

    def create_status_icon(self, topic: str, image: str, text: str = None, accessible_name: str = "Status icon", callback: Any = None) -> HudStatusIcon:
        """Create a status bar icon to be displayed in the status bar widget in the Talon HUD"""
        if callback == None:
            callback = lambda widget, icon: None
        return HudStatusIcon(topic, image, text, accessible_name, callback)

    def create_status_option(self, icon_topic: str, default_option: HudButton, activated_option: HudButton ) -> HudStatusOption:
        """Create a status bar icon to be displayed in the status bar widget in the Talon HUD"""
        return HudStatusOption(icon_topic, default_option, activated_option)

    def create_ability(self, image: str, colour: str, enabled: int, activated: int, image_offset_x: int = 0, image_offset_y: int = 0) -> HudAbilityIcon:
        """Create an icon to be displayed in the ability bar in the Talon HUD"""
        return HudAbilityIcon(image, colour, enabled > 0, 5 if activated > 0 else 0, image_offset_x, image_offset_y)

    def create_panel_content(self, content: str, topic: str = "", title:str = "", show: Union[bool, int] = True, buttons: list[HudButton] = None, voice_commands: Any = None, choices: HudChoices = None) -> HudPanelContent:
        """Create a panel content object for use in the Talon HUD for text or choice display"""            
        if buttons == None:
            buttons = []
            
        commands = []
        if voice_commands == None:
            commands = {}
        else:
            for voice_command in voice_commands:
                commands.append(HudDynamicVoiceCommand(voice_command, voice_commands[voice_command]))
            
        return HudPanelContent(topic, title, [content], buttons, time.time(), show, voice_commands=commands, choices=choices)

    def create_button(self, text: str, callback: Callable[[], None], image: str = "") -> HudButton:
        """Create a button used in the Talon HUD"""
        return HudButton(image, text, ui.Rect(0,0,0,0), callback)
        
    def create_screen_region(self, topic: str, colour: str = None, icon: str = None, title: str = None, hover_visibility: Union[bool, int] = False, x: int = 0, y: int = 0, width: int = 0, height: int = 0, relative_x: int = 0, relative_y: int = 0) -> HudScreenRegion:
        """Create a HUD screen region, where by default it is active all over the available space and it is visible only on a hover"""
        rect = ui.Rect(x, y, width, height) if width * height > 0 else None
        point = Point2d(x + relative_x, y + relative_y)
        return HudScreenRegion(topic, title, icon, colour, rect, point, hover_visibility)

    def create_choices(self, choices_list: list[Any], callback: Callable[[Any], None], multiple: Union[bool, int] = False) -> HudChoices:
        """Creates a list of choices with a single list of dictionaries for the Talon HUD"""
        choices = []
        for index, choice_data in enumerate(choices_list):
            image = choice_data["image"] if "image" in choice_data else ""
            choices.append(HudChoice(image, choice_data["text"], choice_data, "selected" in choice_data and choice_data["selected"], ui.Rect(0,0,0,0)))
        return HudChoices(choices, callback, multiple)

    def create_walkthrough_step(self, content: str, context_hint: str = "", tags: list[str] = None, modes: list[str] = None, app: str = "", restore_callback: Callable[[str], None] = None) -> HudWalkThroughStep:
        """Create a walkthrough step used inside of a walkthrough in the Talon HUD"""
        voice_commands = retrieve_available_voice_commands(content)
        tags = [] if tags is None else tags
        modes = [] if modes is None else modes
        return HudWalkThroughStep(content, context_hint, tags, modes, app, voice_commands, restore_callback)
    
    def create_walkthrough(self, title, walkthrough_steps: list[HudWalkThroughStep]) -> HudWalkThrough:
        """Create a walkthrough for the Talon HUD"""
        return HudWalkThrough(title, walkthrough_steps)
        
    def add_log(self, type: str, message: str, timestamp = None, metadata = None):
        """Adds a log to the HUD"""
        self._content.append_to_log_messages(type, message, timestamp, metadata)
        
    def publish_event(self, topic_type: str, topic:str, operation: str, data: Any = None, show: bool = False, claim: bool = False):
        """Publish created content to the central HUD content object"""
        if topic_type is not None and self._content is not None:
            self._content.publish_event(topic_type, topic, data, operation, show, claim)
    
    def connect(self, content: HeadUpDisplayContent = None):
        """Connect the current content builder to a new central content builder"""
        self._content = content
