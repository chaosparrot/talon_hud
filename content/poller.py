# Base class for dynamic content listening
# This will automatically get enabled and disabled based on the subscribed topics
# If no widgets are there to listen for a specific topic, this poller won't activate
class Poller:
    enabled = False
            
    def enable(self):
        # Attach your event handlers here
        pass

    def disable(self):
        # Detatch your event handlers here    
        pass
