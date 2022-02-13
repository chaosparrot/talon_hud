from .content_builder import HudContentBuilder
from typing import Callable, Any
# Base class for dynamic content listening
# This will automatically get enabled and disabled based on the subscribed topics
# If no widgets are there to listen for a specific topic, this poller won't activate
class Poller:
    enabled = False
    content: HudContentBuilder
            
    def enable(self):
        # Attach your event handlers here
        pass

    def disable(self):
        # Detach your event handlers here    
        pass

    def destroy(self):
        """Destroy references inside of this poller"""
        self.disable()
        if self.content:
            self.content.content = None
            self.content = None