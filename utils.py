from talon import skia
from user.talon_hud.content_types import HudRichText, HudRichTextLine
from textwrap import wrap

def layout_rich_text(paint:skia.Paint, text:str, width:int = 1920, height:int = 1080) -> list[HudRichTextLine]:
    """Layout a string of text inside the given dimensions"""
    
    # Calculate the max characters that fit on a line if we take the largest character A
    # Note - This does cause shorter characters like . from being calculated as taking as much space as A
    _, text_bounds = paint.measure_text("A")
    max_chars_per_line = int( width / text_bounds[0] )
    
    # TODO SEPERATE BASED ON MD STYLES
    lines = text.splitlines()
    final_lines = []
    for line in lines:
        wrapped_lines = wrap(line, max_chars_per_line)
        for wrapped_line in wrapped_lines:
            final_lines.append({
                char_pos: 0,
                width: len(wrapped_line) * text_bounds[0],
                height: text_bounds[1],
                type: 'regular',
                text: wrapped_line
            })
    
    return final_lines
    
def hex_to_ints(hex: str) -> list[int]:
    # Snippet used https://stackoverflow.com/questions/41848722/how-to-convert-hex-str-into-int-array
    return [int(hex[i:i+2],16) for i in range(0,len(hex),2)]
    
def lighten_hex_colour(hex: str, percent: int) -> str:
    ints = hex_to_ints(hex)
    new_hex = ''
    for index, value in enumerate(ints):
        # Skip the opacity channel
        if index <= 2:
            if value < 80:
                value = 80
            value = int(min(255, value * ( 100 + percent ) / 100))
        new_hex += '0' + format(value, 'x') if value <= 15 else format(value, 'x')
    return new_hex