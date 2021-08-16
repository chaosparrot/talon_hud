from talon import skia, ui
from talon.types.point import Point2d
from user.talon_hud.content.typing import HudRichText, HudRichTextLine, HudButton, HudIcon
from textwrap import wrap
import math
import re
import numpy

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
    _, space_text_bounds = paint.measure_text("-")
    
    lines = text.splitlines()
    final_lines = []
    
    styles = []
    for line_index, line in enumerate(lines):        
        current_char_index = 0
        char_indexes = {}
        
        tokened_line = re.split(rich_text_delims_regex, line)
        tokened_line = [x for x in tokened_line if x != ""]
        
        x = 0
        words_to_use = []
        current_line_bounds = None        
        for token in tokened_line:
            if token in rich_text_delims:                
                # Finish the current words if there are any
                if current_line_bounds != None and len(words_to_use) > 0:
                    final_lines.append(HudRichText(x, current_line_bounds.width, current_line_bounds.height, styles.copy(), " ".join(words_to_use)))                
                    x = x + current_line_bounds.width
                    current_line_bounds.width = 0
                    current_line_bounds.height = 0
                words_to_use = []
                if token == '/>':
                    if len(styles) > 0:
                        styles.pop()
                else:
                    styles.append(rich_text_delims_dict[token])
                
            # Add text
            else:
                words = token.split(" ")
                amount_of_words = len(words)
                for index, word in enumerate(words):
                    _, word_bounds = paint.measure_text(word)
                    
                    # Edge case - Space character is split on earlier, so empty strings are space characters that we should include
                    if word == "":
                       word = " "
                       word_bounds.width = space_text_bounds.width                    
                    
                    if index < amount_of_words - 1:
                        word_bounds.width += space_text_bounds.width
                        
                    if current_line_bounds == None:
                        current_line_bounds = word_bounds
                    else:
                        current_line_bounds.width += word_bounds.width
                        current_line_bounds.height = max(word_bounds.height, current_line_bounds.height)
                    
                    if x + current_line_bounds.width - space_text_bounds.width > width:                                            
                        final_lines.append(HudRichText(x, current_line_bounds.width - word_bounds.width, current_line_bounds.height, styles.copy(), " ".join(words_to_use)))
                        x = 0
                        
                        if word_bounds.width < width:
                            words_to_use = [word]
                            current_line_bounds = word_bounds                            
                            
                        # Edgecase - Single word that exceeds the width - Split according to rough estimate or character width
                        else:
                            word_length = len(word)
                            split_ratio = width / word_bounds.width
                            wrapped_words = wrap(word, max(1, int(math.floor(word_length * split_ratio))))
                            for index, wrapped_word in enumerate(wrapped_words):
                                _, wrapped_word_bounds = paint.measure_text(wrapped_word)                            
                                if index < len(wrapped_words) - 1:
                                    final_lines.append(HudRichText(x, wrapped_word_bounds.width, wrapped_word_bounds.height, styles.copy(), wrapped_word))
                                else:
                                    current_line_bounds = wrapped_word_bounds
                                    words_to_use = [wrapped_word]
                            
                    else:
                        words_to_use.append(word) 
                    
        if len(words_to_use) > 0:
            final_lines.append(HudRichText(x, current_line_bounds.width, current_line_bounds.height, styles.copy(), " ".join(words_to_use)))            
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
    
def string_to_speakable_string(str: str) -> str:
    return re.sub(r'([!?-_\,\.])', ' ', str.lower()).strip()
    
def determine_screen_for_pos(pos) -> ui.Screen:
    for index, screen in enumerate(ui.screen.screens()):
        if screen.x <= pos.x and screen.y <= pos.y and screen.x + screen.width >= pos.x \
            and screen.y + screen.height >= pos.y:
            return screen
    
    return None

def linear_gradient(origin_x, origin_y, dest_x, dest_y, colours):
    try:
        return skia.Shader.linear_gradient((origin_x, origin_y), (dest_x, dest_y), colours, None)
    except:
        return skia.Shader.linear_gradient(origin_x, origin_y, dest_x, dest_y, colours, None)

def hit_test_button(button: HudButton, pos: Point2d):
    br = button.rect
    return pos.x >= br.x and pos.x <= br.x + br.width \
        and pos.y >= br.y and pos.y <= br.y + br.height
        
def hit_test_icon(icon: HudIcon, pos: Point2d):
    pos = numpy.array(pos)
    icon_pos = numpy.array(icon.pos)
    return numpy.linalg.norm(pos - icon_pos) < icon.radius