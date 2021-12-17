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
class HudPanelContent:
    topic: str
    title: str
    content: list[str]
    buttons: list[HudButton]
    published_at: float
    show: bool
    choices: HudChoices = None
    tags: list[str] = None
    
@dataclass
class HudScreenRegion:
    topic: str
    title: str = None
    icon: str = None
    colour: str = None
    rect: ui.Rect = None
    point: Point2d = None
    hover_visibility: bool = False

@dataclass
class HudWalkThroughStep:
    content: str = ''
    context_hint: str = ''
    tags: list[str] = None
    modes: list[str] = None
    app: str = ''
    voice_commands: list[str] = None

@dataclass    
class HudWalkThrough:
    title: str
    steps: list[HudWalkThroughStep]