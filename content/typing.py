from dataclasses import dataclass
from talon import ui
from talon.types.point import Point2d
from typing import Callable, Any

@dataclass
class HudRichText:
    x: int
    y: int
    width: int
    height: int
    styles: list[str]
    text: str

class HudRichTextLine: list[HudRichText]

@dataclass
class HudChoice:
    image: str
    text: str
    data: Any
    selected: bool
    rect: ui.Rect
    
@dataclass
class HudChoices:
    choices: list[HudChoice]
    callback: Callable[[Any, Any], None]
    multiple: bool = False

@dataclass
class HudIcon:
    id: str
    image: str
    pos: Point2d
    radius: int
    callback: Callable[[Any], None]

@dataclass
class HudButton:
    image: str
    text: str
    rect: ui.Rect
    callback: Callable[[Any], None]

@dataclass
class HudDynamicVoiceCommand:
    command: str
    callback: Callable[[Any], None]

@dataclass
class HudPanelContent:
    topic: str
    title: str
    content: list[str]
    buttons: list[HudButton]
    published_at: float
    show: bool
    choices: HudChoices = None
    voice_commands: list[HudDynamicVoiceCommand] = None

HOVER_VISIBILITY_ON = 1 # Only show the items when the region is hovered by the mouse
HOVER_VISIBILITY_OFF = 0 # Keep the screen region active regardless of mouse hover
HOVER_VISIBILITY_TRANSPARENT = -1 # Keep the screen region active, but if the mouse hovers over the drawn items, turn them inactive
    
@dataclass
class HudScreenRegion:
    topic: str
    title: str = None
    icon: str = None
    colour: str = None
    rect: ui.Rect = None
    point: Point2d = None
    hover_visibility: int = HOVER_VISIBILITY_OFF
    text_colour: str = None
    vertical_centered: bool = True

# One-indexed page with result
@dataclass
class HudContentPage:
    current: float
    total: float
    percent: float
    
@dataclass
class HudWalkThroughStep:
    content: str = ""
    context_hint: str = ""
    tags: list[str] = None
    modes: list[str] = None
    app: str = ""
    voice_commands: list[str] = None
    restore_callback: Callable[[Any, Any], None] = None
    said_walkthrough_commands: list[str] = None
    progress: HudContentPage = None    
    show_context_hint: bool = False

@dataclass    
class HudWalkThrough:
    title: str
    steps: list[HudWalkThroughStep]

# These content events will be handled automatically
CONTENT_EVENT_OPERATION_REPLACE = "replace" # Used to signal a complete replacement of the given topic
CONTENT_EVENT_OPERATION_REMOVE = "remove" # Used to signal a topic is being cleared
CONTENT_EVENT_OPERATION_DUMP = "dump" # Used to signal a complete replacement all the topics in a widget

# These content events require manual handling from the widgets themselves
CONTENT_EVENT_OPERATION_APPEND = "append" # Used to signal a single item being appended to a collection
CONTENT_EVENT_OPERATION_PATCH = "patch" # Used to signal a partial replacement of the given topic

CLAIM_BROADCAST = 0 # Broadcast to any widget that listens for this topic type
CLAIM_WIDGET = 1 # Claim a single widget and send the content towards it
CLAIM_WIDGET_TOPIC_TYPE = 2 # Claim a single widget and clear out the topic type attached to it

@dataclass
class HudContentEvent:
    topic_type: str
    topic: str
    content: Any
    operation: str = "replace"
    claim: int = CLAIM_BROADCAST
    show: bool = False
    
@dataclass
class HudLogMessage:
    time: float
    type: str
    message: str
    metadata: Any = None
    
@dataclass
class HudAbilityIcon:
    image: str
    colour: str
    enabled: bool
    activated: bool
    image_offset_x: float
    image_offset_y: float

@dataclass
class HudStatusOption:
    icon_topic: str
    default_option: HudButton
    activated_option: HudButton

@dataclass
class HudStatusIcon:
    topic: str
    image: str
    text: str = None
    accessible_text: str = None
    callback: Callable[[Any, Any], None] = None

@dataclass
class HudParticle:
    type: str
    colour: str = None
    image: str = None
    diameter: int = 10
    x: int = 0
    y: int = 0

@dataclass
class HudAudioGroup:
    id: str
    title: str
    description: str
    volume: int = 75
    enabled: bool = False

@dataclass
class HudAudioCue:
    id: str
    group: str
    title: str
    description: str
    file: str
    volume: int = 75
    enabled: bool = False
    
@dataclass
class HudAudioEvent:
    cues: list[str]