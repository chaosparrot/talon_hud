from typing import Callable, Any
from talon import app, Module, actions, Context, speech_system, cron, scope, fs
from .typing import HudWalkThrough, HudWalkThroughStep, HudContentPage
from ..utils import retrieve_available_voice_commands, md_to_richtext_content
from ..configuration import hud_get_configuration
import os
import json
import copy

walkthrough_file_location = os.path.join(hud_get_configuration("content_preferences_folder"), "walkthrough.csv")
initial_walkthrough_title = "Head up display"

mod = Module()
mod.tag("talon_hud_walkthrough", desc="Whether or not the walk through widget is on display")
ctx = Context()

class WalkthroughPoller:
    content = None
    enabled = False
    scope_job = None
    walkthroughs = None
    walkthrough_steps = None
    current_walkthrough = None
    current_walkthrough_title = None
    current_stepnumber = -1
    current_words = []
    in_right_context = True
    development_mode = False
    reload_job = None
    next_step_job = None
    
    def __init__(self):
        self.walkthroughs = {}
        self.walkthrough_files = {}
        self.lazy_walkthroughs = {}
        self.walkthrough_steps = {}
        self.order = []
        
    def set_development_mode(self, enabled):
        self.development_mode = enabled
        self.watch_walkthrough_file(self.development_mode)

    def enable(self):
        if self.enabled == False:
            speech_system.register("pre:phrase", self.check_step)
            self.scope_job = cron.interval("1500ms", self.display_step_based_on_context)
            ctx.tags = ["user.talon_hud_walkthrough"]
            if self.development_mode:
                self.watch_walkthrough_file(True)
        self.enabled = True

    def disable(self):
        if self.enabled == True:
            cron.cancel(self.scope_job)
            self.scope_job = None
            speech_system.unregister("pre:phrase", self.check_step)        
            ctx.tags = []
            if self.development_mode:
                self.watch_walkthrough_file(False)
        self.enabled = False
        
    def watch_walkthrough_file(self, watch=True):
        if self.current_walkthrough_title is not None and self.current_walkthrough_title in self.walkthrough_files:
            current_walkthrough_file = self.walkthrough_files[ self.current_walkthrough_title ]
            fs.unwatch(current_walkthrough_file, self.reload_walkthrough)    
            if watch:
                fs.watch(current_walkthrough_file, self.reload_walkthrough)
        
    def reload_walkthrough(self, _, __):
        cron.cancel(self.reload_job)
        self.reload_job = cron.after("50ms", self.reload_walkthrough_step)
    
    def reload_walkthrough_step(self):
        if self.current_walkthrough is not None:
            self.current_walkthrough.steps = self.lazy_walkthroughs[self.current_walkthrough_title]()
            
            # When the new step count is larger than the current step number, 
            # reset the current step number to the last step
            if self.current_stepnumber >= len(self.current_walkthrough.steps):
                self.current_stepnumber = len(self.current_walkthrough.steps) - 1
                
            if len(self.current_walkthrough.steps) == 0:
                self.end_walkthrough()
            else:
                self.display_step_based_on_context(True)
    
    def load_state(self):
        if not os.path.exists(walkthrough_file_location):
            self.persist_walkthrough_steps(self.walkthrough_steps)

        fh = open(walkthrough_file_location, "r")
        lines = fh.readlines()
        fh.close()
        
        walkthrough_steps = {}
        for index,line in enumerate(lines):
            split_line = line.strip("\n").split(",")
            key = split_line[0]
            current_step = split_line[1]
            total_step = split_line[2]
            walkthrough_steps[key] = {"current": int(current_step), "total": int(total_step), "progress": int(current_step) / int(total_step) if int(total_step) > 0 else 0}
        self.walkthrough_steps = walkthrough_steps
        
        # For the initial loading, start the walkthrough if it hasn"t been completed fully yet
        if initial_walkthrough_title not in self.walkthrough_steps or \
            self.walkthrough_steps[initial_walkthrough_title]["current"] < self.walkthrough_steps[initial_walkthrough_title]["total"]:
            cron.after("1s", self.start_up_hud)

    def persist_walkthrough_steps(self, steps):
        handle = open(walkthrough_file_location, "w")    
    
        walkthrough_items = []
        for key in steps.keys():
            walkthrough_items.append(str(key) + "," + str(steps[key]["current"]) + "," + str(steps[key]["total"]))
        
        if len(walkthrough_items) > 0:
            handle.write("\n".join(walkthrough_items))
        
        handle.close()
        
    def start_up_hud(self):
        """Start up the HUD - Used for the initial walkthrough"""
        actions.user.hud_enable()
        cron.after("1s", self.start_initial_walkthrough)
        
    def start_initial_walkthrough(self):
        """Start the initial walkthrough"""
        self.start_walkthrough(initial_walkthrough_title)
    
    def show_options(self):
        """Show all the available walkthroughs"""
        if len(self.walkthroughs) > 0:
            choice_texts = []
            for title in self.walkthroughs:
                done = title in self.walkthrough_steps and \
                    self.walkthrough_steps[title]["current"] >= self.walkthrough_steps[title]["total"]
                choice_texts.append({"text": title, "selected": done})
            choices = self.content.create_choices(choice_texts, self.pick_walkthrough)
            choice_panel_content = self.content.create_panel_content("Pick a walkthrough from the options below by saying <*option <number>/> or by saying the name.", "walkthrough_options", "Toolkit walkthroughs", True, choices=choices)
            self.content.publish_event("choice", choice_panel_content.topic, "replace", choice_panel_content, True)

    def pick_walkthrough(self, data):
        """Pick a walkthrough from the options menu"""
        self.start_walkthrough(data["text"])
                
    def add_walkthrough_file(self, title: str, filename: str):
        """Add a file that can be loaded in later as a walkthrough"""
        self.walkthrough_files[title] = filename
        self.add_lazy_walkthrough( title, lambda self=self, title=title: self.load_walkthrough_file(title) )
        
    def add_lazy_walkthrough(self, title: str, get_walkthrough: Callable[[], list[HudWalkThroughStep]]):
        """Add a file that can be loaded in later as a walkthrough"""
        self.lazy_walkthroughs[title] = get_walkthrough
        self.add_walkthrough(HudWalkThrough(title, []))
        
    def lazy_load_walkthrough(self, title):
        """Load the walkthrough file"""
        steps = self.lazy_walkthroughs[title]()

        if len(steps) > 0:
            hud_walkthrough.add_walkthrough(HudWalkThrough(title, steps))
        
    def load_walkthrough_file(self, title):
        """Load the walkthrough file"""
        filename = self.walkthrough_files[title]
        walkthrough_defaults = {"content": "", "context_hint": "", "modes": [], "tags": [], "app": ""}
        steps = []
        if filename.endswith(".json"):
            with open(filename) as json_file:
                jsondata = json.load(json_file)
                if isinstance(jsondata, list):
                    for unfiltered_step in jsondata:
                        step = { key: unfiltered_step[key] if key in unfiltered_step else walkthrough_defaults[key] for key in walkthrough_defaults.keys() }
                        walkthrough_step = self.content.create_walkthrough_step(**step)
                        steps.append( walkthrough_step )
        elif filename.endswith(".md"):
            with open(filename) as md_file:
                richtext_content = md_to_richtext_content(md_file.read())
                richtext_lines = richtext_content.splitlines()
                for richtext_line in richtext_lines:
                    if richtext_line != "":
                        step = copy.copy(walkthrough_defaults)
                        step["content"] = richtext_line
                        walkthrough_step = self.content.create_walkthrough_step(**step)
                        steps.append( walkthrough_step )
        return steps
        
    def add_walkthrough(self, walkthrough: HudWalkThrough):
        """Add a walkthrough to the list of walkthroughs"""
        if walkthrough.title not in self.order:
            self.order.append(walkthrough.title)
        self.walkthroughs[walkthrough.title] = walkthrough
     
    def start_walkthrough(self, walkthrough_title: str):
        """Start the given walkthrough if it exists"""
        if walkthrough_title in self.walkthroughs:
            self.end_walkthrough(False)
            self.enable()
            
            # Preload the walkthrough from a file or callback
            if len(self.walkthroughs[walkthrough_title].steps) == 0 and walkthrough_title in self.lazy_walkthroughs:
                self.lazy_load_walkthrough(walkthrough_title)
            
            self.current_walkthrough = self.walkthroughs[walkthrough_title]
            for index, step in enumerate(self.current_walkthrough.steps):
                step.progress = HudContentPage(index, len(self.current_walkthrough.steps), 100 * (index / len(self.current_walkthrough.steps)))
                self.current_walkthrough.steps[index] = step
            
            self.current_walkthrough_title = walkthrough_title
            if self.development_mode:
                self.watch_walkthrough_file(True)
            
            if walkthrough_title in self.walkthrough_steps:
            
                # If we have started a walkthrough but haven"t finished it - continue where we left off
                if walkthrough_title in self.walkthrough_steps and self.walkthrough_steps[walkthrough_title]["current"] < len(self.current_walkthrough.steps):
                    self.current_stepnumber = self.walkthrough_steps[walkthrough_title]["current"] - 1
                # Otherwise, just start over
                else:
                    self.current_stepnumber = -1
            self.next_step()

    def next_step_or_page(self):
        """Navigate to the next step, or the next page in the walkthrough"""
        if self.current_walkthrough is not None:
        
            # Next step also functions as next page on a widget
            pagination = actions.user.hud_get_widget_pagination("walkthrough")
            if pagination.current < pagination.total:
                actions.user.hud_increase_widget_page("walkthrough")
                return
            
            self.next_step()
    
    def next_step(self):
        """Navigate to the next step in the walkthrough"""
        if self.current_walkthrough is not None:
            # Update the walkthrough CSV state
            if self.current_walkthrough.title not in self.walkthrough_steps:
                self.walkthrough_steps[self.current_walkthrough.title] = {"current": 0, "total": len(self.current_walkthrough.steps), "progress": 0}
            self.walkthrough_steps[self.current_walkthrough.title]["current"] = self.current_stepnumber + 1
            self.walkthrough_steps[self.current_walkthrough.title]["progress"] = (self.current_stepnumber + 1) / self.walkthrough_steps[self.current_walkthrough.title]["total"]
            
            self.persist_walkthrough_steps(self.walkthrough_steps)
            self.current_words = []
            
            if self.current_stepnumber + 1 < len(self.current_walkthrough.steps):
                self.transition_to_step(self.current_stepnumber + 1)
                self.walkthrough_steps[self.current_walkthrough.title]["current"] = self.current_stepnumber
                self.walkthrough_steps[self.current_walkthrough.title]["progress"] = (self.current_stepnumber + 1) / self.walkthrough_steps[self.current_walkthrough.title]["total"]

                # If the first step has a restore callback, call that straight away to set the user up
                if self.current_stepnumber == 0 and self.current_walkthrough.steps[0].restore_callback is not None:
                    self.current_walkthrough.steps[self.current_stepnumber].restore_callback(self.current_stepnumber)
            else:
                self.end_walkthrough()
                
    def previous_step(self):
        """Navigate to the previous step in the walkthrough"""
        if self.current_walkthrough is not None:
        
            # Previous step also functions as previous page on a widget
            pagination = actions.user.hud_get_widget_pagination("walkthrough")
            if pagination.current > 1:
                actions.user.hud_decrease_widget_page("walkthrough")
                return

            # Update the walkthrough CSV state
            self.walkthrough_steps[self.current_walkthrough.title]["current"] = max(0, self.current_stepnumber - 1)
            self.walkthrough_steps[self.current_walkthrough.title]["progress"] = max(0, self.current_stepnumber - 1) / self.walkthrough_steps[self.current_walkthrough.title]["total"]
            self.persist_walkthrough_steps(self.walkthrough_steps)
            self.current_words = []
            
            if self.current_stepnumber - 1 >= 0:
                self.transition_to_step(max(0, self.current_stepnumber - 1))
                self.walkthrough_steps[self.current_walkthrough.title]["current"] = self.current_stepnumber
            self.walkthrough_steps[self.current_walkthrough.title]["progress"] = self.current_stepnumber / self.walkthrough_steps[self.current_walkthrough.title]["total"]
        
    def transition_to_step(self, stepnumber):
        """Transition to the next step"""
        self.current_stepnumber = stepnumber
        self.display_step_based_on_context(True)
        
    def restore_walkthrough_step(self):
        """Restore the state of the current walkthrough step"""
        if self.current_walkthrough is not None:
            if self.current_walkthrough.steps[self.current_stepnumber].restore_callback is not None:
                self.current_walkthrough.steps[self.current_stepnumber].restore_callback(self.current_stepnumber)
            else:
                warning_text = "This walkthrough step does not have a restore option."
                if self.current_stepnumber > 0:
                    warning_text += "\nMoving to the previous step."
                    self.previous_step()
                
                self.content.add_log("warning",  warning_text)
        
    def end_walkthrough(self, hide: bool = True):
        """End the current walkthrough"""
        
        # Persist the walkthrough as done
        if hide:
            self.walkthrough_steps[self.current_walkthrough.title]["current"] = len(self.current_walkthrough.steps)
            self.persist_walkthrough_steps(self.walkthrough_steps)
            self.content.publish_event("walkthrough_step", "walkthrough_step", "remove")
            self.content.add_log("event", "Finished the \"" + self.current_walkthrough.title + "\" walkthrough!")

        self.disable()
        self.watch_walkthrough_file(False)
        self.current_walkthrough = None
        self.current_walkthrough_title = None
        self.current_stepnumber = -1
        self.in_right_context = False
    
    def is_in_right_context(self):
        """Check if we are in the right context for the step"""    
        in_right_context = True
        if self.current_walkthrough is not None:
            if self.current_stepnumber < len(self.current_walkthrough.steps):
                step = self.current_walkthrough.steps[self.current_stepnumber]
                tags = scope.get("tag")
                modes = scope.get("mode")
                app_name = scope.get("app")["name"]
                in_correct_tags = set(step.tags) <= tags
                in_correct_modes = set(step.modes) <= modes
                in_correct_app = step.app == ""
                correct_app_names = step.app.split(",")
                for correct_app_name in correct_app_names:
                    if correct_app_name == app_name:
                        in_correct_app = True
                
                in_right_context = in_correct_tags and in_correct_modes and in_correct_app
        return in_right_context
    
    def display_step_based_on_context(self, force_publish = False):
        """Display the correct step information based on the context matching"""
        in_right_context = self.is_in_right_context()
        if self.in_right_context != in_right_context or force_publish:
            step = self.current_walkthrough.steps[self.current_stepnumber]
            step.show_context_hint = not in_right_context
            if not in_right_context:
                self.content.publish_event("walkthrough_step", "walkthrough_step", "replace", copy.copy(step), show=True, claim=True)
            else:
                # Forced publication must clear the voice commands said as well
                # To ensure a clean widget state
                if force_publish:
                    step.said_walkthrough_commands = []
                
                self.content.publish_event("walkthrough_step", "walkthrough_step", "replace", copy.copy(step), show=True, claim=True)
            self.in_right_context = in_right_context
    
    def check_step(self, phrase):
        """Check if contents in the phrase match the voice commands available in the step"""
        if self.current_walkthrough is not None and self.is_in_right_context():
            phrase_to_check = " ".join(phrase["phrase"]).lower()
            if self.current_stepnumber < len(self.current_walkthrough.steps):
                step = self.current_walkthrough.steps[self.current_stepnumber]
                
                current_length = len(self.current_words)
                for index, voice_command in enumerate(step.voice_commands):
                    # Make sure the activations can only happen in-order
                    if index >= current_length:
                        if voice_command in phrase_to_check:
                            self.current_words.append(voice_command)
                            phrase_to_check = phrase_to_check.split(voice_command, 1)[1]
                        else:
                            break
                
                # Send an update about the voice commands said during the step if it has changed
                if current_length != len(self.current_words):
                    step.said_walkthrough_commands = self.current_words[:]
                    self.content.publish_event("walkthrough_step", "walkthrough_step", "replace", copy.copy(step), show=True, claim=True)
                    
                    # Skip to the next step if no voice commands are available
                    voice_commands_remaining = copy.copy(step.voice_commands)
                    all_commands_said = False
                    for said_word in self.current_words:
                        if said_word in voice_commands_remaining:
                            voice_commands_remaining.remove(said_word)
                    
                    if len(step.voice_commands) > 0 and len(voice_commands_remaining) == 0 and not "skip step" in step.voice_commands and not "continue" in step.voice_commands:
                        cron.cancel(self.next_step_job)
                        self.next_step_job = cron.after("1500ms", self.next_step)
    
hud_walkthrough = WalkthroughPoller()
hud_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_walkthrough():
    global hud_walkthrough
    actions.user.hud_add_walkthrough("Head up display", hud_directory + "/docs/hud_walkthrough.json")
    actions.user.hud_add_poller("walkthrough_step", hud_walkthrough)
    hud_walkthrough.load_state()

app.register("ready", load_walkthrough)

@mod.action_class
class Actions:

    def hud_add_walkthrough(title: str, filename: str):
        """Add a walk through through a file"""
        global hud_walkthrough 
        hud_walkthrough.add_walkthrough_file(title, filename)
        
    def hud_add_lazy_walkthrough(title: str, get_walkthrough: Callable[[], list[HudWalkThroughStep]]):
        """Add a walk through through a file"""
        global hud_walkthrough 
        hud_walkthrough.add_lazy_walkthrough(title, get_walkthrough)

    def hud_create_walkthrough_step(content: str, context_hint: str = "", tags: list[str] = None, modes: list[str] = None, app: str = "", restore_callback: Callable[[Any, Any], None] = None):
        """Create a step for a walk through"""
        voice_commands = retrieve_available_voice_commands(content)
        tags = [] if tags is None else tags
        modes = [] if modes is None else modes
        return HudWalkThroughStep(content, context_hint, tags, modes, app, voice_commands, restore_callback)

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
        hud_walkthrough.next_step_or_page()
        
    def hud_previous_walkthrough_step():
        """Skip the current walk through step"""
        global hud_walkthrough
        hud_walkthrough.previous_step()
        
    def hud_skip_walkthrough_all():
        """Skip the current walk through step"""
        global hud_walkthrough
        hud_walkthrough.end_walkthrough()
        
    def hud_restore_walkthrough_step():
        """Restore the current walkthrough step if possible"""
        global hud_walkthrough
        hud_walkthrough.restore_walkthrough_step()
        
    def hud_watch_walkthrough_files():
        """Enable watching for changes in the walkthrough files for quicker development"""
        global hud_walkthrough
        hud_walkthrough.set_development_mode(True)
        
    def hud_unwatch_walkthrough_files():
        """Disable watching for changes in the walkthrough files for quicker development"""
        global hud_walkthrough
        hud_walkthrough.set_development_mode(False)
        
    def hud_show_walkthroughs():
        """Show all the currently available walk through options"""
        global hud_walkthrough
        hud_walkthrough.show_options()
