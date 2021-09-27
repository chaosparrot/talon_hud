from talon import app, Module, actions, Context, registry, speech_system, cron
from user.talon_hud.content.typing import HudWalkThrough, HudWalkThroughStep
from user.talon_hud.utils import retrieve_available_voice_commands
import os

mod = Module()
mod.tag("talon_hud_walkthrough", desc="Whether or not the walk through widget is on display")
ctx = Context()

class HeadUpWalkthroughState:

    scope_job = None

    walkthroughs = None
    current_walkthrough = None
    current_stepnumber = -1
    
    def __init__(self):
        self.walkthroughs = {}
        self.order = []
    
    def show_options(self):
        if len(self.walkthroughs) > 0:
            # TODO ADD CHOICE LIST OF WALK THROUGHS
            pass
        
    def add_walkthrough(self, walkthrough: HudWalkThrough):
        """Add a walkthrough to the list of walkthroughs"""    
        if walkthrough.title not in self.order:
            self.order.append(walkthrough.title)
        self.walkthroughs[walkthrough.title] = walkthrough

    def start_walkthrough(self, walkthrough_title: str):
        """Start the given walkthrough if it exists"""
        if walkthrough_title in self.walkthroughs:            
            self.end_walkthrough(False)
            speech_system.register("post:phrase", self.check_step)
            self.scope_job = cron.interval('1500ms', self.check_context)
            ctx.tags = ["user.talon_hud_walkthrough"]
            self.current_walkthrough = self.walkthroughs[walkthrough_title]
            actions.user.enable_hud_id("walk_through")            
            self.next_step()

    def next_step(self):
        """Navigate to the next step in the walkthrough"""
        if self.current_walkthrough is not None:
            if self.current_stepnumber + 1 < len(self.current_walkthrough.steps):
                self.transition_to_step(self.current_stepnumber + 1)
            else:
                self.end_walkthrough()
        
    def transition_to_step(self, stepnumber):
        """Transition to the next step"""
        self.current_stepnumber = stepnumber
        actions.user.hud_publish_content(self.current_walkthrough.steps[stepnumber].content, "walk_through")        
        
    def end_walkthrough(self, hide: bool = True):
        """End the current walkthrough"""
        cron.cancel(self.scope_job)
        self.scope_job = None
        speech_system.unregister("post:phrase", self.check_step)
        self.current_walkthrough = None
        self.current_stepnumber = -1
        ctx.tags = []
        if hide:
            actions.user.hud_publish_content("No walk through started", "walk_through")
            actions.user.disable_hud_id("walk_through")
    
    def check_context(self):
        if self.current_walkthrough is not None:
            if self.current_stepnumber in self.current_walkthrough.steps:
                step = self.current_walkthrough.steps[self.current_stepnumber]
                # Check if we are in the right context here
        print( "YEET" )
    
    def check_step(self, phrase):
        if self.current_walkthrough is not None:
            if self.current_stepnumber in self.current_walkthrough.steps:
                step = self.current_walkthrough.steps[self.current_stepnumber]
                
        print(" ".join(phrase['phrase']).lower())
    
hud_walkthrough = HeadUpWalkthroughState()

def add_walkthrough():
    steps = []
    steps.append( actions.user.hud_create_walkthrough_step("Welcome to Talon HUD!\nThis is a short walk through of the content available.\nSay <cmd@skip step/> to move to the next step."))
    steps.append( actions.user.hud_create_walkthrough_step("Enter the next step by saying <cmd@yeet/>"))
    walkthrough = actions.user.hud_create_walkthrough("Head up display", steps)
    hud_walkthrough.start_walkthrough('Head up display')    

app.register('ready', add_walkthrough)


@mod.action_class
class Actions:
    content: str = ''
    documentation_content: str = ''
    context_explanation: str = ''
    tags: list[str] = None
    modes: list[str] = None
    voice_commands: list[str] = None
    app_title: str = ''

    def hud_create_walkthrough_step(content: str, documentation_content: str = '', context_explanation: str = '', tags: list[str] = None, modes: list[str] = None, app_title: str = ''):
        """Create a step for a walk through"""
        voice_commands = retrieve_available_voice_commands(content)
        return HudWalkThroughStep(content, documentation_content, context_explanation, tags, modes, app_title, voice_commands)

    def hud_create_walkthrough(title: str, steps: list[HudWalkThroughStep]):
        """Create a walk through with all the required steps"""
        global hud_walkthrough 
        hud_walkthrough.add_walkthrough(HudWalkThrough(title, steps))

    def hud_start_walkthrough(title: str):
        """Starts a loaded in walk through"""
        global hud_walkthrough
        hud_walkthrough.start_walkthrough(title)

    def hud_skip_walkthrough_step():
        """Skip the current walk through step"""
        global hud_walkthrough
        hud_walkthrough.next_step()
        
    def hud_skip_walkthrough_all():
        """Skip the current walk through step"""
        global hud_walkthrough
        hud_walkthrough.end_walkthrough()
        
    def hud_show_walkthroughs():
        """Show all the currently available walk through options"""
        global hud_walkthrough
        hud_walkthrough.show_options()