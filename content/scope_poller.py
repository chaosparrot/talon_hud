from talon import actions, cron, scope, ui, app, Module
from .poller import Poller

# Polls the current Talon scope for debugging purposes
class ScopePoller(Poller):
    content = None
    job = None
    previous_scope_state = ""
    should_open = False

    def enable(self):
       if (self.job is None):
            self.enabled = True
            self.should_open = True            
            self.job = cron.interval("100ms", self.state_check)
                
    def disable(self):
        cron.cancel(self.job)
        self.job = None
        self.enabled = False

    def state_check(self):        
        scope_state = self.get_state_in_text()
        if (scope_state != self.previous_scope_state):
            self.previous_scope_state = scope_state
            panel_content = self.content.create_panel_content(scope_state, "scope", "Toolkit scope", self.should_open)
            self.content.publish_event("text", panel_content.topic, "replace", panel_content, self.should_open, True)
            self.should_open = False
        
    def get_state_in_text(self):
        tags = scope.get("tag")
        
        new_tags = []
        if tags is not None:
            for tag in tags:
                new_tags.append(tag)
                
        modes = []
        scopemodes = scope.get("mode")
        if scopemodes is not None:
            for mode in scopemodes:
                modes.append(mode)
                
        text = "<*App: " + scope.get("app")["name"] + "/> " + scope.get("win")["title"] + "/>\n<*Tags:/>\n" + "\n".join(sorted(new_tags)) + "\n<*Modes:/> " + " - ".join(sorted(modes))
        return text
                
def append_poller():
    actions.user.hud_add_poller("scope", ScopePoller())
app.register("ready", append_poller)

mod = Module()
@mod.action_class
class Actions:

    def hud_toolkit_scope():
        """Start debugging the Talon scope in the Talon HUD"""
        actions.user.hud_add_poller("scope", ScopePoller())
        actions.user.hud_activate_poller("scope")
