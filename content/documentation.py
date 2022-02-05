from talon import app, actions, Module, cron, fs
import os
from ..utils import md_to_richtext_content

mod = Module()

class HeadUpDocumentation:
    order = None
    files = None
    descriptions = None
    current_title = None
    reload_job = None
    development_mode = False
    
    def __init__(self):
        self.files = {}
        self.descriptions = {}
        self.order = []
    
    def add_file(self, title: str, description: str, filename: str):
        if os.path.isfile(filename):
            self.files[title] = filename
            if description:
                self.descriptions[title] = description
                
            if title not in self.order:
                self.order.append(title)
        else:
            app.notify(filename + " could not be found")

    def load_documentation(self, title: str):
        if title in self.files:
            if self.development_mode:
                self.watch_documentation_file(False)
            
            self.current_title = title
            
            if self.development_mode:
                self.watch_documentation_file(True)
            
            text_file = open(self.files[title], "r")
            documentation = text_file.read()
            text_file.close()
            if self.files[title].endswith(".md"):
                documentation = md_to_richtext_content(documentation)
            actions.user.hud_publish_content(documentation, "documentation", title)

    def show_overview(self):
        documentation = "Say any of the bolded titles below to open the documentation\n\n"
        for index, order in enumerate(self.order):
            documentation += "<* " + str(index + 1) + " - " + order + "/>"
            if order in self.descriptions:
                documentation += ": " + self.descriptions[order]
            documentation += "\n"

        voice_commands = {}
        for title in self.order:
            voice_commands[title] = lambda self=self, title=title: self.load_documentation(title)
        actions.user.hud_publish_content(documentation, "documentation", "Documentation panel", True, [], voice_commands)
        if self.development_mode:
            self.watch_documentation_file(False)
        self.current_title = None

    def set_development_mode(self, enabled):
        self.development_mode = enabled
        self.watch_documentation_file(self.development_mode)
    
    def watch_documentation_file(self, watch=True):
        if self.current_title is not None:
            fs.unwatch(self.files[self.current_title], self.debounce_reload_documentation)    
            if watch:
                fs.watch(self.files[self.current_title], self.debounce_reload_documentation)
                
    def debounce_reload_documentation(self, _, __):
        cron.cancel(self.reload_job)
        self.reload_job = cron.after("50ms", self.reload_documentation)
    
    def reload_documentation(self):
        if self.current_title is not None:
            self.load_documentation(self.current_title)

hud_documentation = HeadUpDocumentation()

@mod.action_class
class Actions:

    def hud_add_documentation(title: str, description: str, filename: str):
        """Add a file to the documentation panel of the Talon HUD"""
        global hud_documentation
        hud_documentation.add_file(title, description, filename)
        
    def hud_watch_documentation_files():
        """Enable watching for changes in the documentation files for quicker development"""
        global hud_documentation
        hud_documentation.set_development_mode(True)
        
    def hud_unwatch_documentation_files():
        """Disable watching for changes in the documentation files for quicker development"""
        global hud_documentation
        hud_documentation.set_development_mode(False)
        
    def hud_show_documentation(title: str = ""):
        """Show the general documentation"""
        global hud_documentation
        if title == "":
            hud_documentation.show_overview()
        else:
            hud_documentation.load_documentation(title)
        
