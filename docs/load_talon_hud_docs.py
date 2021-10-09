from talon import scope, app, actions
import os

def talon_hud_ready():
    # Check if Talon HUD is available to the user
    if "user.talon_hud_available" in scope.get('tag'):
    
        # Get the absolute path to the documentation directory for your package
        documentation_dir = str(os.path.dirname(os.path.abspath(__file__)))
        
        # Add an item to the Toolkit documentation page
        actions.user.hud_add_documentation("Widget settings", 
            "shows the general Talon HUD commands related to widgets",
            documentation_dir + "/hud_widget_documentation.txt")

        # Add a walkthrough to the Toolkit walkthrough options
        actions.user.hud_add_walkthrough('Head up display', 
            documentation_dir + '/hud_walkthrough.json')

app.register('ready', talon_hud_ready)