from talon import skia, ui
from user.talon_hud.content_types import HudRichText, HudRichTextLine
from textwrap import wrap
import re

rich_text_delims_dict = {
    '/>': 'end', # GENERAL STYLE END - We only use a single token for this to not have to deal with issues where nested styles get changed out of order
    '<*': 'bold', # BOLD STYLE
    '</': 'italic', # ITALIC STYLE
    '<+': 'success', # COLOUR
    '<!!': 'error', # COLOUR
    '<!': 'warning', # COLOUR
    '<@': 'notice', # COLOUR
}
rich_text_delims = rich_text_delims_dict.keys()
rich_text_delims_regex = r'(/>|<\*|</|<\+|<\!\!|<\!|<@)'

def remove_tokens_from_rich_text(text:str):
    return re.sub(rich_text_delims_regex, '', text)

def layout_rich_text(paint:skia.Paint, text:str, width:int = 1920, height:int = 1080) -> list[HudRichTextLine]:
    """Layout a string of text inside the given dimensions"""
    
    # Calculate the max characters that fit on a line if we take an average character b
    # Note - This does cause shorter characters like . or larger ones like A to be calculated as taking as much space as t
    # To account for this, we take a small amount of pixels away from the total width to make sure the odds of wider glyphs clipping are reduced
    _, text_bounds = paint.measure_text("B")
    max_chars_per_line = int( width / text_bounds.width )
    
    lines = text.splitlines()
    final_lines = []
    
    styles = []
    for line in lines:
        replaced_line = re.sub(rich_text_delims_regex, '', line)
        
        # No rich text style change - Just do a simple line wrapping
        if len(replaced_line) == len(line):
            wrapped_lines = wrap(line, max_chars_per_line)
            for wrapped_line in wrapped_lines:
                _, line_text_bounds = paint.measure_text(wrapped_line)
                final_lines.append(HudRichText(0, line_text_bounds.width, text_bounds.height, styles.copy(), wrapped_line))        
        
        # Rich text style change! Seperate the text out into tokens
        else:
            current_char_index = 0
            char_indexes = {}
            
            tokened_line = re.split(rich_text_delims_regex, line)
            tokened_line = [x for x in tokened_line if x != ""]
            untokened_line = "".join([x for x in tokened_line if x not in rich_text_delims])
            
            wrapped_lines = wrap(untokened_line, max_chars_per_line)
            rich_tokens_done = 0            
            for wrapped_line in wrapped_lines:
                rich_token_index = 0            
                start_of_line = current_char_index
                end_of_line = current_char_index + len(wrapped_line)
                x_pos = 0
                
                token_char_index = 0
                for token in tokened_line:
                    total_token_length = len(token)
                    rich_token_index = rich_token_index if token not in rich_text_delims else rich_token_index + 1
                    if current_char_index > end_of_line or ( token in rich_text_delims and rich_tokens_done >= rich_token_index ):
                        continue
                    else:
                        # Add styling
                        if token in rich_text_delims:
                            if token == '/>':
                                if len(styles) > 0:
                                    styles.pop()
                            else:
                                styles.append(rich_text_delims_dict[token])
                            rich_tokens_done += 1
                                
                        # Add text
                        else:
                            token_to_use = wrapped_line[token_char_index:token_char_index + len(token)]
                            
                            # Split the token up if the length of the string exceeds that of the wrapped line
                            token_length = len(token_to_use)
                            current_char_index += token_length
                            _, line_text_bounds = paint.measure_text(token_to_use)
                            token_char_index += token_length
                            textwidth = line_text_bounds.width + text_bounds.width if token_to_use.endswith(" ") else line_text_bounds.width
                            final_lines.append(HudRichText(x_pos, textwidth, text_bounds.height, styles.copy(), token_to_use))
                            x_pos += int(round(textwidth, 2))
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
    
def determine_screen_for_pos(pos) -> ui.Screen:
    for index, screen in enumerate(ui.screen.screens()):
        if screen.x <= pos.x and screen.y <= pos.y and screen.x + screen.width >= pos.x \
            and screen.y + screen.height >= pos.y:
            return screen
    
    return None
    