from talon import actions, cron, scope
from talon.scripting import Dispatch
import time

max_log_length = 50

# Contains the state of the content inside of the head up display
# Widget data like hover states are contained within the widget
# NOTE - THIS USES A TALON API THAT IS SUBJECT TO CHANGE AND MIGHT BREAK IN FUTURE VERSIONS
class HeadUpDisplayContent(Dispatch):

    # Default content to be displayed
    content = {
        'mode': 'command',
        'language': {
            'ext': None,
            'forced': False
        }
    }
    
    # Event log for things like history etc.
    log = []
        
    # Update the content and sends an event if the state has changed
    def update(self, dict):
        updated = False
        for key in dict:
            if (key in self.content):
                if not updated and self.content[key] != dict[key]:
                    updated = True
                self.content[key] = dict[key]
            
            if (key not in self.content):
                updated = True
                self.content[key] = dict[key]
        
        if updated:
            self.dispatch("content_update", self.content)
        
    def append_to_log(self, type, log_message):
        self.log.append({'type': type, 'message': log_message, 'time': time.monotonic()})
        self.log[-max_log_length:]
        self.dispatch("log_update", self.log)
        
hud_content = HeadUpDisplayContent()