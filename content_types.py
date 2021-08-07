from talon import ui
from typing import TypedDict
from dataclasses import dataclass

class HudIcon(TypedDict):
    type: str
    image: str
    clickable: bool
    explanation: str

@dataclass
class HudRichText:
    x: int
    width: int
    height: int
    styles: list[str]
    text: str
    
class HudRichTextLine: list[HudRichText]

@dataclass
class HudButton:
    icon: str
    type: str
    text: str
    rect: ui.Rect

@dataclass
class HudPanelContent:
    purpose: str
    title: str
    content: list[str]
    buttons: list[HudButton]
    published_at: float
    show: bool