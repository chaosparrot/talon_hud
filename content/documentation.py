from talon import app, Module, actions, Context
import os

mod = Module()
mod.tag("talon_hud_documentation_overview", desc="Whether or not the documentation overview is on display")
mod.list("talon_hud_documentation_title", desc="List of titles of added documentation in Talon HUD")

ctx = Context()

class HeadUpDocumentation:
    order = None
    files = None
    descriptions = None
    
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
                ctx.lists['user.talon_hud_documentation_title'] = self.order
        else:
            app.notify(filename + " could not be found")

    def load_documentation(self, title: str):
        if title in self.files:
            text_file = open(self.files[title], "r")
            documentation = text_file.read()
            text_file.close()
            actions.user.hud_publish_content(documentation, "documentation", title)

    def show_overview(self):
        documentation = "Say any of the bolded titles below to open the documentation\n\n"
        for index, order in enumerate(self.order):
            documentation += "<* " + str(index + 1) + " - " + order + "/>"
            if order in self.descriptions:
                documentation += ": " + self.descriptions[order]
            documentation += "\n"
        
        actions.user.hud_publish_content(documentation, "documentation", "Documentation panel", True, [], ["user.talon_hud_documentation_overview"])

hud_documentation = HeadUpDocumentation()

@mod.action_class
class Actions:

    def hud_add_documentation(title: str, description: str, filename: str):
        """Add a file to the documentation panel of the Talon HUD"""
        global hud_documentation
        hud_documentation.add_file(title, description, filename)
        
    def hud_show_documentation(title: str = ""):
        """Show the general documentation"""
        global hud_documentation
        if title == "":
            hud_documentation.show_overview()
        else:
            hud_documentation.load_documentation(title)
        