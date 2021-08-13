from talon import actions, cron, scope, ui, app, Module
from user.talon_hud.content.poller import Poller

# Polls the current Talon scope for debugging purposes
class ScopePoller(Poller):
    job = None
    previous_scope_state = ''

    def enable(self):
       if (self.job is None):
            self.enabled = True
            # Open the widget initially
            scope_state = self.get_state_in_text()        
            actions.user.hud_publish_content(scope_state, 'scope', 'Scope panel')        
            
            self.job = cron.interval('100ms', self.state_check)
                
    def disable(self):
        cron.cancel(self.job)
        self.job = None
        self.enabled = False

    def state_check(self):        
        scope_state = self.get_state_in_text()
        if (scope_state != self.previous_scope_state):
            self.previous_scope_state = scope_state
            actions.user.hud_publish_content(scope_state, 'scope', 'Scope panel', False)
        
    def get_state_in_text(self):
        tags = scope.get('tag')
        
        new_tags = []
        if tags is not None:
            for tag in tags:
                new_tags.append(tag)
                
        modes = []
        scopemodes = scope.get('mode')
        if scopemodes is not None:
            for mode in scopemodes:
                modes.append(mode)
                
        text = "<*<@App: " + scope.get('app')['name'] + "/>/>\n" + scope.get('win')['title'] + "/>\n<*<@Tags:/>/>\n" + "\n".join(sorted(new_tags)) + "\n<*<@Modes:/>/>  " + " - ".join(sorted(modes))
        return text

mod = Module()
@mod.action_class
class Actions:

    def debug_scope():
        """Start debugging the Talon scope in the Talon HUD"""
        actions.user.hud_add_poller('scope', ScopePoller())
        actions.user.hud_activate_poller('scope')
