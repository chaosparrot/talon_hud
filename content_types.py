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