from user.talon_hud.base_widget import BaseWidget
from talon import skia, ui, Module, cron, actions
import time
import numpy
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences
from user.talon_hud.utils import layout_rich_text

class HeadUpEventLog(BaseWidget):

    subscribed_content = ["mode"]
    content = {
        'mode': 'command'
    }
    subscribed_logs = ['*']
    allowed_setup_options = ["position", "dimension", "limit", "font_size"]    
    
    visual_logs = []
    visual_log_length = 0

    # By default - This widget sits just above the statusbar on the right side of the screen
    # Which means more screen real estate is on the left and top which is why we want the alignment to the right and the expand direction to go up
    # Also assume the logs should be read chronologically from top to bottom, 
    # Which means new messages push old messages up if they haven't disappeared yet
    preferences = HeadUpDisplayUserWidgetPreferences(type="event_log", x=1430, y=720, width=450, height=200, enabled=True, alignment="right", expand_direction="up", font_size=18)

    # TODO - For the downward direction we need to pop earlier messages if the height is exceeded to make room for newer logs

    ttl_animation_max_duration = 10
    animation_max_duration = 60 # Keep it the same as the status bar for now

    soft_enabled = True
    show_animations = True

    ttl_animation_duration_seconds = 1.0
    ttl_duration_seconds = 9
    ttl_poller = None

    def append_log(self, log):
        if self.soft_enabled and self.enabled and len(log['message']) > 0:
            visual_log = {
                "ttl": log["time"] + self.ttl_duration_seconds, 
                "type": log["type"], 
                "message": log["message"], 
                "animation_tick": self.ttl_animation_max_duration if self.show_animations else 0, 
                "animation_goal": 0
            }
            
            if (self.expand_direction == "up"):
                self.visual_logs.insert(0, visual_log)
            else:
                self.visual_logs.append(visual_log)
            self.poll_ttl_visuals()
            
            # Poll for TTL expiration at half the rate of the animation duration - It's not mission critical to make the logs disappear at exactly the right time
            if self.ttl_poller is None:
                self.ttl_poller = cron.interval(str(int(self.ttl_animation_duration_seconds / 2 * 1000)) +'ms', self.poll_ttl_visuals)

    # Clean out all the logs still visible on the screen
    def disable(self, persisted=False):
        if self.enabled:
            self.soft_disable()
            super().disable(persisted)
            
            cron.cancel(self.ttl_poller)
            self.ttl_poller = None
            
    def enable(self, persisted=False):
        if not self.enabled:
            self.soft_enabled = self.content['mode'] == 'command'
            super().enable(persisted)

    def clear(self):
        super().clear()
        self.visual_logs = []

    # Clean out all the logs still visible on the screen    
    def soft_disable(self):
        self.soft_enabled = False
        current_time = time.monotonic()
        
        # Set the TTL to all non-expired messages            
        if self.show_animations:
            for visual_log in self.visual_logs:
                if visual_log["ttl"] - self.ttl_animation_duration_seconds > current_time and visual_log["animation_tick"] >= 0:
                    visual_log['ttl'] = current_time + self.ttl_animation_duration_seconds
                    visual_log["animation_tick"] = -1
                    visual_log["animation_goal"] = -self.ttl_animation_max_duration
        # Just clear all the logs if not animated
        else:
            self.visual_logs = []            

    def refresh(self, new_content):
        # We only want the logs to appear during command mode
        # Dictation mode already shows the output directly as dictation
        # And we want to reduce screen clutter during sleep mode
        if ("mode" in new_content and new_content["mode"] != self.content['mode']):
            if (new_content["mode"] != "command"):
                self.soft_disable()
            else:
                self.soft_enabled = True

    def poll_ttl_visuals(self):
        current_time = time.monotonic()
        
        resume_canvas = self.visual_log_length != len(self.visual_logs)
        for visual_log in self.visual_logs:
            if self.show_animations and visual_log["ttl"] - self.ttl_animation_duration_seconds <= current_time and visual_log["animation_tick"] >= 0:
                visual_log["animation_tick"] = -1
                visual_log["animation_goal"] = -self.ttl_animation_max_duration
                resume_canvas = True
        
        # Clear the logs marked for deletion
        self.visual_logs = [visual_log for visual_log in self.visual_logs if visual_log["ttl"] > current_time ]

        # Only start drawing when changes have been made
        if resume_canvas and self.enabled:
            self.canvas.resume()

        self.visual_log_length = len(self.visual_logs)
        if self.visual_log_length == 0 and self.ttl_poller is not None:
            self.canvas.resume()
            cron.cancel(self.ttl_poller)
            self.ttl_poller = None

    def draw(self, canvas) -> bool:
        paint = self.draw_setup_mode(canvas)
            
        # Clear logs that are no longer visible    
        self.visual_logs = [visual_log for visual_log in self.visual_logs if not (visual_log["animation_tick"] < 0 and visual_log["animation_tick"] == visual_log["animation_goal"]) ]
        self.visual_log_length = len(self.visual_logs)
        
        if (self.visual_log_length > 0):
            paint.textsize = self.font_size
            continue_drawing = False

            default_background_colour = self.theme.get_colour('event_log_background', 'F5F5F5')
            background_colour = default_background_colour
            log_margin = 10
            text_padding = 8
            vertical_text_padding = 4
            log_height = 30
            
            current_y = self.y if self.expand_direction == "down" else self.y + self.height
            for index, visual_log in enumerate(self.visual_logs):
            
                
            
                # Split up the text into lines if there are linebreaks
                # And calculate their dimensions
                # TODO calculate max text width against the width and see if we need to wrap the text to the next line
                # TODO emphasis text using **Md bold markers**
                lines = layout_rich_text(paint, visual_log['message'], self.limit_width, self.limit_height)
                #lines = visual_log['message'].splitlines()
                total_text_width = 0
                total_text_height = 0
                for line in lines:
                    total_text_width = max( total_text_width, line.width )
                    total_text_height = total_text_height + line.height + vertical_text_padding
                log_height = vertical_text_padding * (1 + len(lines)) + total_text_height
            
                if self.expand_direction == "down":                    
                    offset = 0 if index == 0 else log_margin + log_height
                    current_y = current_y + offset
                else:
                    offset = log_height if index == 0 else log_margin + log_height
                    current_y = current_y - offset
                
                text_width = total_text_width
                element_width = text_padding * 2 + text_width

                text_x = self.x + text_padding if self.alignment == "left" else self.x + self.width - text_padding - text_width
                element_x = text_x - text_padding
                
                # Fade the opacity of the message
                opacity = 1.0 if visual_log['animation_tick'] >= 0 else 0.0
                if (visual_log['animation_tick'] != visual_log['animation_goal'] ):
                    continue_drawing = True
                    if visual_log['animation_tick'] < visual_log['animation_goal']:
                        visual_log['animation_tick'] = visual_log['animation_tick'] + 1
                    else:
                        visual_log['animation_tick'] = visual_log['animation_tick'] - 1
                    opacity = ( self.ttl_animation_max_duration - abs(visual_log['animation_tick']) ) / self.ttl_animation_max_duration
                
                max_opacity = self.theme.get_opacity('event_log_opacity')
                text_colour = self.theme.get_colour('event_log_text_colour', self.theme.get_colour('text_colour') )                
                if visual_log['type'] != "event":
                    background_colour = default_background_colour
                else:
                    background_colour = self.theme.get_colour('info_colour', '30AD9E')
                    max_opacity = 255
                    text_colour = 'FFFFFF'
                opacity_int = min(max_opacity, int(max_opacity * opacity))
                opacity_hex = hex(opacity_int)[-2:] if opacity_int > 15 else '0' + hex(opacity_int)[-1:]
                
                paint.color = background_colour + opacity_hex
                self.draw_background(canvas, element_x, current_y, element_width, log_height, paint)
                
                # Draw text line by line
                max_text_opacity = self.theme.get_opacity('event_log_text_opacity', 1.0)
                opacity_int = min(max_text_opacity, int(max_text_opacity * opacity))
                opacity_hex = hex(opacity_int)[-2:] if opacity_int > 15 else '0' + hex(opacity_int)[-1:]
                paint.color = text_colour + opacity_hex
                
                line_height = total_text_height / len(lines)
                for index, line in enumerate(lines):
                    canvas.draw_text(line.text, text_x, current_y + line_height + index * vertical_text_padding + index * line_height )
                
            return continue_drawing
        else:
            return False
        
    def draw_animation(self, canvas, animation_tick):
        if self.enabled:
            return True
        else:
            return self.draw(canvas)

    def draw_background(self, canvas, origin_x, origin_y, width, height, paint):
        radius = 5
        rect = ui.Rect(origin_x, origin_y, width, height)
        rrect = skia.RoundRect.from_rect(rect, x=radius, y=radius)
        canvas.draw_rrect(rrect)