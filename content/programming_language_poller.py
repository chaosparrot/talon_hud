from talon import actions, cron, scope, app, Module
from .poller import Poller
from .._configuration import hud_get_configuration
import os

languages = {}

class ProgrammingLanguagePoller(Poller):
    enabled = False
    content = None
    job = None
    current_language = None
    can_toggle = False
    
    def enable(self):
        if not self.enabled:
            self.job = cron.interval("200ms", self.language_check)
            self.enabled = True

    
    def disable(self):
        if self.enabled:
            self.enabled = False
            cron.cancel(self.job)
            self.job = None
            
    def language_check(self):
        global languages
        can_toggle = actions.user.hud_can_toggle_programming_language()
        language = actions.user.hud_get_programming_language()
        
        if self.current_language != language or can_toggle != self.can_toggle:
            self.current_language = language
            self.can_toggle = can_toggle
            if language != "":
                icon = ""
                text = ""
                if language in languages:
                    icon = languages[language]["icon"]
                    text = languages[language]["extension"]
                
                callback = False
                if can_toggle:
                    callback = lambda _, _2: actions.user.hud_toggle_programming_language()
                status_icon = self.content.create_status_icon("programming_toggle", icon, text, language + " detected", callback)
                self.content.publish_event("status_icons", status_icon.topic, "replace", status_icon)
            else:
                status_icon = self.content.create_status_icon("programming_toggle", "", "", "No programming language detected", False)
                self.content.publish_event("status_icons", status_icon.topic, "replace", status_icon)


def add_statusbar_programming_icon(_ = None):
    actions.user.hud_activate_poller("programming_toggle")
    
def remove_statusbar_programming_icon(_ = None):
    actions.user.hud_deactivate_poller("programming_toggle")
    actions.user.hud_remove_status_icon("programming_toggle")

def register_language_poller():
    actions.user.hud_add_poller("programming_toggle", ProgrammingLanguagePoller())
    default_option = actions.user.hud_create_button("Add code language", add_statusbar_programming_icon, "text_navigation")
    activated_option = actions.user.hud_create_button("Remove code language", remove_statusbar_programming_icon, "text_navigation")
    status_option = actions.user.hud_create_status_option("programming_toggle", default_option, activated_option)
    actions.user.hud_publish_status_option("programming_option", status_option)

app.register("ready", register_language_poller)

def load_languages(languages_file):
    languages = {}
    languages_header = "Language,Extension,Icon"
    if not os.path.exists(languages_file):
        language_defaults = [
            "bash,.sh,programming_bash",
            "c,,programming_c",
            "cplusplus,.cpp,programming_cplusplus",
            "csharp,.cs,programming_cplusplus",
            "objectivec,,programming_objectivec",
            "haskel,.hs,programming_haskel",
            "swift,,programming_swift",
            "rust,.rs,programming_rust",
            "r,.r,programming_r",
            "php,.php,programming_php",
            "ruby,.rb,programming_ruby",
            "python,.py,programming_python",
            "lua,.lua,programming_lua",
            "html,.html,programming_html",
            "javascript,.js,programming_javascript",
            "typescript,.ts,programming_typescript",
            "perl,.pl,programming_perl",
            "json,.json,programming_json",
            "markdown,.md,programming_markdown",
            "yaml,.yml,"
        ]
        file_contents = "" + languages_header
        file_contents += "\n".join(language_defaults)
        with open(languages_file, "w") as f:
            f.write(file_contents)    

    with open(languages_file, "r") as file:
        for line in file.readlines():
            if line == languages_header:
                continue
            split_vars = line.strip().split(",")
            if len(split_vars) > 1:
                language = {}
                language["extension"] = split_vars[1]
                if len(split_vars) > 2:
                    language["icon"] = split_vars[2]
                else:
                    language["icon"] = ""
                languages[split_vars[0]] = language
    return languages

languages_file = os.path.join(hud_get_configuration("content_preferences_folder"), "programming_languages.csv")
languages = load_languages(languages_file)

mod = Module()
@mod.action_class
class Actions:

    def hud_can_toggle_programming_language() -> bool:
        """Check if we should be able to toggle the programming language from the status bar"""
        return False

    def hud_toggle_programming_language():
        """Toggle the programming language manually in the status bar"""
        pass
        
    def hud_get_programming_language() -> str:
        """Get the programming language to be displayed in the status bar - By default tries to mimic knausj"""
        lang = actions.code.language()
        if not lang:
            active_modes = scope.get("mode")
            if (active_modes is not None):
                for index, active_mode in enumerate(active_modes):
                    if (active_mode.replace("user.", "") in languages.keys()):
                        return active_mode.replace("user.", "")
            active_tags = scope.get("tag")
            if (active_tags is not None):
                for index, active_tag in enumerate(active_tags):
                    if (active_tag.replace("user.", "") in languages.keys()):
                        return active_tag.replace("user.", "")
            return ""
        else:
            return lang if lang else ""

