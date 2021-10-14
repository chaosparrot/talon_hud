from talon import scope, app, actions
import os

def talon_hud_ready():
    # Check if Talon HUD is available to the user
    if "user.talon_hud_available" in scope.get("tag"):
    
        # Get the absolute path to the documentation directory for your package
        documentation_dir = str(os.path.dirname(os.path.abspath(__file__)))
        
        # Add an item to the Toolkit documentation page
        actions.user.hud_add_documentation("Widget settings", 
            "shows the general Talon HUD commands related to widgets",
            documentation_dir + "/hud_widget_documentation.txt")

        # Add a walkthrough to the Toolkit walkthrough options
        actions.user.hud_add_walkthrough("Head up display", 
            documentation_dir + "/hud_walkthrough.json")
        
        # Dictation
        actions.user.hud_add_walkthrough("Basic sentence dictation", 
            documentation_dir + "/dictation_walkthrough.json")
        
        # Browser documentation
        actions.user.hud_add_documentation("Browser usage", 
            "shows the commands and explanations related to web browser usage",
            documentation_dir + "/browser_usage_documentation.txt")
            
        # Basic browser usage
        actions.user.hud_add_walkthrough("Basic browser usage", 
            documentation_dir + "/basic_browser_usage_walkthrough.json")
            
        # Media usage
        actions.user.hud_add_walkthrough("Music and video controls", 
            documentation_dir + "/music_and_video_walkthrough.json")
            

app.register("ready", talon_hud_ready)