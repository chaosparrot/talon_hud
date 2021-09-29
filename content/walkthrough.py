from talon import app, Module, actions, Context, speech_system, cron, scope
from user.talon_hud.content.typing import HudWalkThrough, HudWalkThroughStep
from user.talon_hud.utils import retrieve_available_voice_commands
import os

semantic_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
walkthrough_file_location = semantic_directory + "/preferences/walkthrough.csv"
initial_walkthrough_title = "Head up display"

mod = Module()
mod.tag("talon_hud_walkthrough", desc="Whether or not the walk through widget is on display")
ctx = Context()

class HeadUpWalkthroughState:

    scope_job = None
    walkthroughs = None
    walkthrough_steps = None    
    current_walkthrough = None
    current_stepnumber = -1
    current_words = []
    in_right_context = True
    
    def __init__(self):
        self.walkthroughs = {}
        self.walkthrough_steps = {}
        self.order = []
    
    def load_state(self):
        if not os.path.exists(walkthrough_file_location):
            self.persist_walkthrough_steps(self.walkthrough_steps)

        fh = open(walkthrough_file_location, "r")
        lines = fh.readlines()
        fh.close()
        
        walkthrough_steps = {}
        for index,line in enumerate(lines):
            split_line = line.strip('\n').split(',')
            key = split_line[0]
            value = split_line[1]
            walkthrough_steps[key] = int(value)
        self.walkthrough_steps = walkthrough_steps
        
        # For the initial loading, start the walkthrough if it hasn't been completed fully yet
        if initial_walkthrough_title not in self.walkthrough_steps or \
            self.walkthrough_steps[initial_walkthrough_title] < len(self.walkthroughs[initial_walkthrough_title].steps):
            cron.after('1s', self.start_up_hud)

    def persist_walkthrough_steps(self, steps):
        handle = open(walkthrough_file_location, "w")    
    
        walkthrough_items = []
        for key in steps.keys():
            walkthrough_items.append(str(key) + "," + str(steps[key]))
        
        if len(walkthrough_items) > 0:
            handle.write("\n".join(walkthrough_items))
        
        handle.close()
        
    def start_up_hud(self):
        """Start up the HUD - Used for the initial walkthrough"""
        actions.user.enable_hud()
        cron.after('2s', self.start_initial_walkthrough)
        
    def start_initial_walkthrough(self):
        """Start the initial walkthrough"""    
        self.start_walkthrough(initial_walkthrough_title)
    
    def show_options(self):
        """Show all the available walkthroughs"""
        if len(self.walkthroughs) > 0:
            choice_texts = []
            for title in self.walkthroughs:
                done = title in self.walkthrough_steps and \
                    self.walkthrough_steps[title] >= len(self.walkthroughs[title].steps)
                choice_texts.append({"text": title, "selected": done})
            choices = actions.user.hud_create_choices(choice_texts, self.pick_walkthrough)
            actions.user.hud_publish_choices(choices, "Walkthrough options", 
                "Pick a walkthrough from the options below by saying <*option <number>/> or by saying the name.")

    def pick_walkthrough(self, data):
        """Pick a walkthrough from the options menu"""
        self.start_walkthrough(data["text"])
        
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
            self.scope_job = cron.interval('1500ms', self.display_step_based_on_context)
            ctx.tags = ["user.talon_hud_walkthrough"]
            self.current_walkthrough = self.walkthroughs[walkthrough_title]
            actions.user.enable_hud_id("walk_through")
            if walkthrough_title in self.walkthrough_steps:
            
                # If we have started a walkthrough but haven't finished it - continue where we left off
                if self.walkthrough_steps[walkthrough_title] < len(self.current_walkthrough.steps):
                    self.current_stepnumber = self.walkthrough_steps[walkthrough_title] - 1                    
                # Otherwise, just start over
                else:
                    self.current_stepnumber = -1
            self.next_step()

    def next_step(self):
        """Navigate to the next step in the walkthrough"""
        if self.current_walkthrough is not None:

            # Update the walkthrough CSV state
            self.walkthrough_steps[self.current_walkthrough.title] = self.current_stepnumber + 1                        
            self.persist_walkthrough_steps(self.walkthrough_steps)
            self.current_words = []
            
            if self.current_stepnumber + 1 < len(self.current_walkthrough.steps):
                self.transition_to_step(self.current_stepnumber + 1)
                self.walkthrough_steps[self.current_walkthrough.title] = self.current_stepnumber
            else:
                self.end_walkthrough()
        
    def transition_to_step(self, stepnumber):
        """Transition to the next step"""
        self.current_stepnumber = stepnumber
        self.display_step_based_on_context(True)
        
    def end_walkthrough(self, hide: bool = True):
        """End the current walkthrough"""
        
        # Persist the walkthrough as done
        if hide:
            self.walkthrough_steps[self.current_walkthrough.title] = len(self.current_walkthrough.steps)
            self.persist_walkthrough_steps(self.walkthrough_steps)
            actions.user.hud_set_walkthrough_voice_commands([])
            actions.user.hud_publish_content("No walk through started", "walk_through")
            actions.user.disable_hud_id("walk_through")
            actions.user.hud_add_log("event", "Finished the \"" + self.current_walkthrough.title + "\" walkthrough!")

        cron.cancel(self.scope_job)
        self.scope_job = None
        speech_system.unregister("post:phrase", self.check_step)
        self.current_walkthrough = None
        self.current_stepnumber = -1
        ctx.tags = []
        self.in_right_context = False
    
    def is_in_right_context(self):
        """Check if we are in the right context for the step"""    
        in_right_context = True
        if self.current_walkthrough is not None:
            if self.current_stepnumber < len(self.current_walkthrough.steps):
                step = self.current_walkthrough.steps[self.current_stepnumber]
                tags = scope.get('tag')
                modes = scope.get('mode')
                app_name = scope.get('app')['name']                
                in_correct_tags = set(step.tags) <= tags
                in_correct_modes = set(step.modes) <= modes
                in_correct_app = True                
                in_correct_app = step.app == "" or step.app in app_name
                in_right_context = in_correct_tags and in_correct_modes and in_correct_app
        return in_right_context
    
    def display_step_based_on_context(self, force_publish = False):
        """Display the correct step information based on the context matching"""
        in_right_context = self.is_in_right_context()
        if self.in_right_context != in_right_context or force_publish:
            step = self.current_walkthrough.steps[self.current_stepnumber]        
            if not in_right_context:
                actions.user.hud_publish_content(step.context_explanation, "walk_through")            
            else:
                actions.user.hud_publish_content(step.content, "walk_through")
            self.in_right_context = in_right_context
    
    def check_step(self, phrase):
        """Check if contents in the phrase match the voice commands available in the step"""
        if self.current_walkthrough is not None and self.is_in_right_context():
            phrase_to_check = " ".join(phrase['phrase']).lower()
            if self.current_stepnumber < len(self.current_walkthrough.steps):
                step = self.current_walkthrough.steps[self.current_stepnumber]
                
                current_length = len(self.current_words)
                for voice_command in step.voice_commands:
                    if voice_command in phrase_to_check and voice_command not in self.current_words:
                        self.current_words.append(voice_command)
                
                # Send an update about the voice commands said during the step if it has changed
                if current_length != len(self.current_words):
                    actions.user.hud_set_walkthrough_voice_commands(list(self.current_words))
                
    
hud_walkthrough = HeadUpWalkthroughState()

def load_walkthrough():
    steps = []
    steps.append( actions.user.hud_create_walkthrough_step("Welcome to Talon HUD!\nThis is a short walkthrough of the content available.\nSay <*skip step/> to move to the next step."))
    steps.append( actions.user.hud_create_walkthrough_step("Talon HUD has a bunch of content hidden behind a central hub called Toolkit.\nTo see what is inside, say <cmd@toolkit options/>", '', 
    'Please enable the command mode by clicking on the statusbar icon', [], ['command']))
    steps.append( actions.user.hud_create_walkthrough_step("Toolkit has an overview of the content available, like documentation, walkthroughs and some debugging helpers. \nFor instance, if you say <cmd@talon scope/> it will open up a text panel containing the current scope!", '', 
    'Please enable the command mode by clicking on the statusbar icon', [], ['command']))    
    walkthrough = actions.user.hud_create_walkthrough("Head up display", steps)
    
    steps = []
    steps.append( actions.user.hud_create_walkthrough_step("What if we could document our workflows using walkthroughs?!\n\n<cmd@air/>  <cmd@bat/>  <cmd@cap/>  <cmd@drum/>\n"))
    steps.append( actions.user.hud_create_walkthrough_step("Hey it transitions to a new step when all the commands are said! <cmd@each/> <cmd@fine/>\n"))
    steps.append( actions.user.hud_create_walkthrough_step("\"But Chaos\" I hear you think, \"What if the user is in the wrong context? The commands won't work!\". <cmd@gust/>", '', 
    'Please enable command mode before continuing', [], ['command']))
    steps.append( actions.user.hud_create_walkthrough_step("\"Hmm.. but what if the user cannot say or does not want to say the command?\".\n<cmd@Like and subscribe to my youtube channel lmao/>"))
    walkthrough = actions.user.hud_create_walkthrough("Alphabet", steps)
    
    hud_walkthrough.load_state()

app.register('ready', load_walkthrough)

@mod.action_class
class Actions:

    def hud_create_walkthrough_step(content: str, documentation_content: str = '', context_explanation: str = '', tags: list[str] = None, modes: list[str] = None, app: str = ''):
        """Create a step for a walk through"""
        voice_commands = retrieve_available_voice_commands(content)
        tags = [] if tags is None else tags
        modes = [] if modes is None else modes
        return HudWalkThroughStep(content, documentation_content, context_explanation, tags, modes, app, voice_commands)

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