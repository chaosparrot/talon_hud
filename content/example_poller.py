from talon import actions, cron, app, Module

# Starts counting whenever it is enabled
class CountingPoller:
    enabled = False
    content = None
    counting_job = None
    current_count = 0
    topic = "counting"

    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.publish_count() # Immediately publish the current count to the HUD
            self.counting_job = cron.interval("1s", self.count_up) # Increase the count every second
    
    def disable(self):
        if self.enabled:
            self.enabled = False
            # Clean up all the counting related crons/ registered events
            cron.cancel(self.counting_job)

    def count_up(self):
        self.current_count += 1
        self.publish_count()

    def publish_count(self):
        topic = self.topic # The topic to publish
        topic_type = "status_icons" # The type of topic to publish
        icon = None # The status bar icon, in this case, we do not want any
        text = str(self.current_count) # The text to display in the status bar
        accessible_text = text + " is the current count" # Accessible text that can in the future be used for screen readers
        status_icon = self.content.create_status_icon(topic, icon, text, accessible_text )
        self.content.publish_event("status_icons", self.topic, "replace", status_icon)

    # Disable the counting on the status bar completely
    # As the topic is removed from the widget, the poller won't restart when the widget is enabled again
    def disable_counting(self):
        self.disable()
        self.current_count = 0
        
        # Remove the topic and the content from the status bar
        self.content.publish_event("status_icons", self.topic, "remove")

# Create a single poller that we can use in action definitions below
counting_poller = CountingPoller()

# Register the poller to the HUD whenever the file is reloaded
def append_poller():
    actions.user.hud_add_poller(counting_poller.topic, counting_poller)
app.register("ready", append_poller)

# Add actions to bind in a .talon file
mod = Module()
@mod.action_class
class Action:

    def start_counting():
        """Starts counting on the Talon HUD status bar"""
        global counting_poller
        actions.user.hud_activate_poller(counting_poller.topic)

    def pause_counting():
        """Pauses the counting on the Talon HUD status bar"""
        global counting_poller
        actions.user.hud_deactivate_poller(counting_poller.topic)
        
    def stop_counting():
        """Removes the counting from the status bar"""
        global counting_poller
        counting_poller.disable_counting()