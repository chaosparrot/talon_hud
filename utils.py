from talon import skia, ui
from talon.types.point import Point2d
from .content.typing import HudRichText, HudRichTextLine, HudButton, HudIcon
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
    
    # Semantic information
    '<cmd@': 'command_available', # Voice command available
}
rich_text_delims = rich_text_delims_dict.keys()
rich_text_delims_regex = r'(/>|<\*|</|<\+|<\!\!|<\!|<@|<cmd@)'

def remove_tokens_from_rich_text(text:str):
    return re.sub(rich_text_delims_regex, '', text)
    
def retrieve_available_voice_commands(text: str):
    voice_commands = []
    tokened_text = re.split( rich_text_delims_regex, text)
    tokened_text = [x for x in tokened_text if x != ""]
    words_to_use = []
    
    styles = []
    for token in tokened_text:
        if token in rich_text_delims:
            if token == '/>':
                if len(styles) > 0:
                    in_voice_command = "command_available" in styles
                    styles.pop()
                    if in_voice_command and "command_available" not in styles and len(words_to_use) > 0:
                        voice_commands.append(string_to_speakable_string(" ".join(words_to_use)))
                        words_to_use = []                        
            else:
                if rich_text_delims_dict[token] == "command_available" and \
                    "command_available" not in styles:
                    words_to_use = []
                styles.append(rich_text_delims_dict[token])
        else:
            words_to_use += token.split()
        
    # Edge case - Clean up remaining commands        
    if "command_available" in styles:
        voice_commands.append(string_to_speakable_string(" ".join(words_to_use)))
    
    # Sort commands by length so that shorter commands do not take away words from a longer command
    voice_commands.sort(key=len, reverse=True)
    
    return voice_commands

def layout_rich_text(paint:skia.Paint, text:str, width:int = 1920, height:int = 1080) -> list[HudRichTextLine]:
    """Layout a string of text inside the given dimensions"""
    _, e_text_bounds = paint.measure_text("E")
    _, space_text_bounds = paint.measure_text("E E")
    space_text_bounds.width -= e_text_bounds.width * 2
    
    lines = text.splitlines()
    final_lines = []
    
    styles = []
    for line_index, line in enumerate(lines):        
        current_char_index = 0
        char_indexes = {}
        
        tokened_line = re.split(rich_text_delims_regex, line)
        tokened_line = [x for x in tokened_line if x != ""]
            
        x = 0
        
        # Edge case - Empty newline
        if len(tokened_line) == 0:
            final_lines.append(HudRichText(x, space_text_bounds.y, space_text_bounds.width, space_text_bounds.height, [], " "))
            continue
        
        words_to_use = []
        current_line_bounds = None
        for token in tokened_line:
            if token in rich_text_delims:                
                # Finish the current words if there are any
                if current_line_bounds != None and len(words_to_use) > 0:
                    current_line_bounds = calculate_words_bounds(words_to_use, paint, space_text_bounds)
                    final_lines.append(HudRichText(x, current_line_bounds.y, current_line_bounds.width, current_line_bounds.height, styles.copy(), " ".join(words_to_use)))                
                    x = x + current_line_bounds.width
                    current_line_bounds.y = current_line_bounds.y
                    current_line_bounds.width = 0
                    current_line_bounds.height = 0
                words_to_use = []
                if token == '/>':
                    if len(styles) > 0:
                        styles.pop()
                        
                    # Unbold the text for the proper height measurements
                    if "bold" not in styles:
                        paint.font.embolden = False
                else:
                    # Bold the text for the proper height measurements
                    if rich_text_delims_dict[token] == "bold":                        
                        paint.font.embolden = True
                    styles.append(rich_text_delims_dict[token])
                
            # Add text
            else:
                words = token.split(" ")
                current_words = []
                amount_of_words = len(words)
                for index, word in enumerate(words):
                    current_words.append(word)
                    
                    # Edge case - string starts with a space
                    if word == "" and len(current_words) == 0:
                        current_line_bounds = space_text_bounds
                        word_bounds = space_text_bounds
                    else:
                        _, word_bounds = paint.measure_text(word)
                        current_line_bounds = calculate_words_bounds(current_words, paint, space_text_bounds)
                    
                    if x + current_line_bounds.width > width:
                        current_words.pop()
                        current_line_bounds = calculate_words_bounds(current_words, paint, space_text_bounds)
                        final_lines.append(HudRichText(x, current_line_bounds.y, current_line_bounds.width, current_line_bounds.height, styles.copy(), " ".join(words_to_use)))
                        x = 0
                        y = 0
                        
                        if word_bounds.width < width:
                            current_words = [word]
                            words_to_use = [word]
                            
                        # Edgecase - Single word that exceeds the width - Split according to rough estimate or character width
                        else:
                            word_length = len(word)
                            split_ratio = width / word_bounds.width
                            wrapped_words = wrap(word, max(1, int(math.floor(word_length * split_ratio))))
                            for index, wrapped_word in enumerate(wrapped_words):
                                _, wrapped_word_bounds = paint.measure_text(wrapped_word)                            
                                if index < len(wrapped_words) - 1:
                                    final_lines.append(HudRichText(x, wrapped_word_bounds.y, wrapped_word_bounds.width, wrapped_word_bounds.height, styles.copy(), wrapped_word))
                                else:
                                    current_line_bounds = wrapped_word_bounds
                                    words_to_use = [wrapped_word]
                            
                    else:
                        words_to_use.append(word)
                    
        if len(words_to_use) > 0:
            current_line_bounds = calculate_words_bounds(words_to_use, paint, space_text_bounds)
        
            final_lines.append(HudRichText(x, current_line_bounds.y, current_line_bounds.width, current_line_bounds.height, styles.copy(), " ".join(words_to_use)))            
    
    paint.font.embolden = False
    return final_lines

def md_to_richtext_content(md_string: str):
    sanitized_content = sanitize_md_from_unsupported_tags(md_string)
    
    # Marks to be translated to the internal rich text delimiters
    mark_voice_command = "-MARK-VOICE-COMMAND-"
    mark_italic = "-MARK-ITALIC-"
    mark_italic_u = "-MARK-U-ITALIC-"    
    mark_emphasis = "-MARK-EMPHASIS-"
    mark_emphasis_u = "-MARK-U-EMPHASIS-"
    mark_error = "-MARK-ERROR-"
    
    # Escaped marks
    escaped_backtick = "-ESCAPED-BACKTICK-"
    escaped_star = "-ESCAPED-STAR-"
    escaped_underscore = "-ESCAPED-UNDERSCORE-"
    
    # Keep escaped characters around
    md_content = sanitized_content.replace("\\`", escaped_backtick).replace("\\*", escaped_star).replace("\\_", escaped_underscore)\
        .replace(" ` ", " " + escaped_backtick + " ").replace(" * ", " " + escaped_star + " ").replace(" _ ", " " + escaped_underscore + " ")
    content_escaped = len(md_content) != len(sanitized_content)
    
    # Replace all the MD markers
    md_content = md_content.replace("!!", mark_error)            
    md_content = md_content.replace("__", mark_emphasis_u).replace("**", mark_emphasis)
    md_content = md_content.replace("_", mark_italic_u).replace("*", mark_italic)
    md_content = md_content.replace(mark_emphasis + mark_emphasis_u, mark_emphasis + mark_italic_u)\
    	.replace(mark_emphasis_u + mark_emphasis, mark_emphasis_u + mark_italic)            
    md_content = md_content.replace("```", "`").replace("`", mark_voice_command)
    
    # This is probably a highly inefficient way of replacing tokens, but it should probably be atleast consistent?
    md_content = replace_md_content_mark(md_content, mark_voice_command, "<cmd@")
    md_content = replace_md_content_mark(md_content, mark_error, "<!!")
    md_content = replace_md_content_mark(md_content, mark_italic, "</")
    md_content = replace_md_content_mark(md_content, mark_italic_u, "</")
    md_content = replace_md_content_mark(md_content, mark_emphasis, "<*")
    md_content = replace_md_content_mark(md_content, mark_emphasis_u, "<*")
    
    # Only unescape the content if we have escaped
    if content_escaped:
        md_content = md_content.replace(escaped_backtick, "`").replace(escaped_star, "*").replace(escaped_underscore, "_")
            
    return md_content

def replace_md_content_mark(md_content: str, mark_to_replace: str, token: str) -> str:
    mark_opened = False
    token_splits = md_content.split(mark_to_replace)
    if len(token_splits) > 0:
        replaced_content = token_splits[0]
        for split_token in token_splits[1:]:
            mark_opened = not mark_opened
            replaced_content += ( token if mark_opened else "/>" ) + split_token
        md_content = replaced_content
    return md_content

def sanitize_md_from_unsupported_tags(md_content: str) -> str:
    content = []
    lines = md_content.splitlines()
    line_added = False
    
    for line in lines:
        stripped_line = line.strip()
        
        # Skip all headers
        # Skip all table rows
        # Skip all block quotes
        if stripped_line.startswith("#") or \
            stripped_line.startswith("|") or \
            stripped_line.startswith(">"):
            content_added = False
            continue
		    
        # Skip all horizontal lines and remove the previous line before it if it has been added
        elif ( "-" in stripped_line and not len(stripped_line.replace("-", "")) > 0) or \
            ( "=" in stripped_line and not len(stripped_line.replace("=", "")) > 0):
            if content_added:
                content.pop()
                content_added = False		    
            continue
        elif line == "":
            content.append(line)
            
            # Empty lines need to be marked as no content to allow the header removal to work properly
            content_added = False
        else:
            content.append(line)
            content_added = True
    return "\n".join(content)    

def calculate_words_bounds(words: list[str], paint, space_text_bounds) -> ui.Rect:
    current_words_joined = " ".join(words)
    _, current_line_bounds = paint.measure_text(current_words_joined)            
    
    # Edge case - dealing with single space
    if len(words) == 1 and words[0] == "":
        current_line_bounds = space_text_bounds
    else:
        leading_spaces_count = len(current_words_joined) - len(current_words_joined.lstrip(' '))
        trailing_spaces_count = len(current_words_joined) - len(current_words_joined.rstrip(' '))
        extra_spaces_count = leading_spaces_count + trailing_spaces_count
        
        # Edge case - Spaces only
        if len(current_words_joined.lstrip(' ')) == 0:
            extra_spaces_count = leading_spaces_count
        current_line_bounds.width += extra_spaces_count * space_text_bounds.width

    return current_line_bounds
    
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
    return hit_test_rect(br, pos)
        
def hit_test_rect(rect: ui.Rect, pos: Point2d):
    return pos.x >= rect.x and pos.x <= rect.x + rect.width \
        and pos.y >= rect.y and pos.y <= rect.y + rect.height
        
def hit_test_icon(icon: HudIcon, pos: Point2d):
    pos = numpy.array(pos)
    icon_pos = numpy.array(icon.pos)
    return numpy.linalg.norm(pos - icon_pos) < icon.radius
    
def is_light_colour(red: int, green: int, blue: int) -> bool:
    luminance = (.299 * red) + (.587 * green) + (.114 * blue)
    return luminance > 40

