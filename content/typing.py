from dataclasses import dataclass
from talon import ui
from talon.types.point import Point2d
from typing import Callable, Any

@dataclass
class HudRichText:
    x: int
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
    spoken_alias: str
    rect: ui.Rect
    
@dataclass
class HudChoices:
    choices: list[HudChoice]
    callback: Callable[[Any, Any], None]

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
    purpose: str
    title: str
    content: list[str]
    buttons: list[HudButton]
    published_at: float
    show: bool