from talon import actions, cron, scope, app, Module
from .poller import Poller

class LanguagePoller(Poller):
    enabled = False
    content = None
    job = None
    current_language = None
    
    def enable(self):
        if not self.enabled:
            self.enabled = True
            self.job = cron.interval("200ms", self.language_check)            
    
    def disable(self):
        if self.enabled:
            self.enabled = False
            cron.cancel(self.job)
            self.job = None
            self.current_language = None

    def language_check(self):
        language = self.detect_language()
        if self.current_language != language:
            self.current_language = language
            status_icon = self.content.create_status_icon("language_toggle", language, None, "Language " + language, lambda _, _2, language=language: actions.user.hud_toggle_language(language))
            self.content.publish_event("status_icons", status_icon.topic, "replace", status_icon)

    def detect_language(self):
        language = scope.get("language", "en_US")
        if isinstance(language, str):
            return language

        for lang in language:
            if "_" in lang:
                return lang

def add_statusbar_language_icon(_ = None):
    actions.user.hud_activate_poller("language_toggle")
    
def remove_statusbar_language_icon(_ = None):
    actions.user.hud_deactivate_poller("language_toggle")
    actions.user.hud_remove_status_icon("language_toggle")

def register_language_poller():
    actions.user.hud_add_poller("language_toggle", LanguagePoller())

    default_option = actions.user.hud_create_button("Add language", add_statusbar_language_icon, "en_US")
    activated_option = actions.user.hud_create_button("Remove language", remove_statusbar_language_icon, "en_US")
    status_option = actions.user.hud_create_status_option("language_toggle", default_option, activated_option)
    actions.user.hud_publish_status_option("language_option", status_option)

app.register("ready", register_language_poller)

mod = Module()
@mod.action_class
class Actions:

    def hud_toggle_language(current_language: str = "en_US"):
        """Toggles the current language to another language"""
        print( "No default toggle available - Build your own language toggle by overriding user.hud_toggle_language" )
        pass