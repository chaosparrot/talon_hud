# Talon HUD Content

The content inside of the HUD is meant to be mostly customizable and creatable by you. Stuff like available modes, programming languages and can be tweaked to match your specific needs.  
Creating text content is straight forward and can be done in .talon files for the simple use cases, and in python for the more advanced usecases.  
There is also other content like status bar icons, logs and screen regions, that have special requirements.

For more advanced cases, there is also "sticky" content, which is content that can stick around in between restarts. An example of this is the mode or microphone icon on the status bar, but things like the scope debugging are sticky content as well. On the bottom of the page is an explanation on how to make your own sticky content.

## Content customization

### Customizing mode tracking

You can customize three things about the mode tracking
1. The icons connected to the modes. These are stored in the themes folder as <modename>_icon.png and can be changed there.
2. The mode that should be displayed on the status bar.
3. The toggle functionality of the mode tracking button.

Below is an example of the last two being customized, where only the command and sleep icon are displayed, instead of having the dictation icon displayed as well.

```python
from talon import Context, actions, scope

ctx = Context()
ctx.matches = """
tag: user.talon_hud_available
"""

@ctx.action_class("user")
class Actions:

    def hud_determine_mode() -> str:
        """Determine the current mode used for the status bar icons and the widget states"""
        active_modes = scope.get("mode")
        available_modes = ["command", "sleep"]
        
        current_mode = "command"
        for available_mode in available_modes:
            if available_mode in active_modes:
                current_mode = available_mode
                break
        
        return current_mode

    def hud_toggle_mode():
        """Toggle the current mode to a new mode"""
        current_mode = actions.user.hud_determine_mode()
        if current_mode in ["command"]:
             actions.speech.disable()
        elif current_mode == "sleep":
             actions.speech.enable()
```

### Customizing language tracking

You can customize two things about the language tracking
1. The language icons shown in the status bar - These are images with the language names inside of the themes images folder.
2. The action that is executed when you click on the language icon

By default, there is no action tied to the language icon, but you can add one yourself by tweaking the example below.

```python
from talon import Context, actions, scope

ctx = Context()
ctx.matches = """
tag: user.talon_hud_available
"""

@ctx.action_class("user")
class Actions:

    def hud_toggle_language(current_language: str = "en_US"):
        """Toggles the current language to another language"""
        actions.user.hud_add_log("warning", "Clicked the language " + current_language + " icon!")
```

### Customizing programming languages

In the programming language visualisation, you can change a couple of things:

1. The available programming languages - These are kept in preferences/programming_languages.csv.
- The first column is the programming language.
- The second column is the extension, this will be shown as text if no icon is available.
- The icon file name of the programming language.
2. The programming language icons - These are kept in the images folder inside themes.
3. The language detection code
4. The toggle functionality of the icon

An example of the last two where only the tags and not the modes are referenced for the language are kept down below.
Also, in this example, clicking on the programming language makes the language show up in the event log with a different colour.

```python
from talon import Context, actions, scope

ctx = Context()
ctx.matches = """
tag: user.talon_hud_available
"""

@ctx.action_class("user")
class Actions:
    def hud_can_toggle_programming_language() -> bool:
        """Check if we should be able to toggle the programming language from the status bar"""
        return True

    def hud_toggle_programming_language():
        """Toggle the programming language manually in the status bar"""
        language = actions.user.hud_get_programming_language()
        type = "success" if language == "python" else "error"
        actions.user.hud_add_log(type, "The current language is " + actions.user.hud_get_programming_language())

    def hud_get_programming_language() -> str:
        """Get the programming language to be displayed in the status bar - By default tries to mimic knausj"""
        lang = actions.code.language()
        if not lang:
            languages = actions.user.hud_get_available_languages()
            active_tags = scope.get("tag")
            if (active_tags is not None):
                for index, active_tag in enumerate(active_tags):
                    if (active_tag.replace("user.", "") in languages.keys()):
                        return active_tag.replace("user.", "")
            return ""
        else:
            return lang if lang else ""
```

## Creating text content

Publishing to a single text panel is easy and can be done either through a .talon file, or in a python file
An example where a simple hello world text is published is placed below. `hello world talon` is purely inside a talon file, `hello world python` is a connection between the .talon file and the python file.

```talon
hello world talon: user.hud_publish_content("Hello world example", "example", "Hello world")
hello world python: user.hud_example_text()
```

```python
from talon import Module, actions

mod = Module()
@mod.action_class
class Actions:
    
	def hud_example_text():
	    """This is an example action for HUD documentation purposes"""
		actions.user.hud_publish_content("Hello world example", "example", "Hello world")
```

You can also place rich text inside of the content.

These will apply styling to the text within them. Rich text needs to be opened with a style marker and closed with a closing marker.  
Bold and italic markers can be active at the same time. For the colours, only the latest will count.

In order to create text like this: 
I want to **try out** rich text!

You have to type this:
``` 
'I want to <*try out/> rich text!
``` 

The following styling markers are available:
- <* : Bold text
- </ : Italic text
- <+ : Text in the colour green, used for success messages and other successful actions
- <! : Text in the colour orange, used for warning users
- <!! : Text in the colour red, used for errors
- <@ : Text in the colour blue, used to notify the user.
- <cmd@ : Denotes the start of a voice command that can be said - Not all widgets have a specific style for this
- /> : Closing marking - ends the latest style applied

When writing rich text containing voice commands, make sure to emphasise the voice commands with one of these markers so they stand out from the rest of the text.  
This makes it easier for the user to quickly pick out the voice commands from the text you have written.  
There isn't a firm styling for voice commands yet, so for now just apply a bold marker at the minimum until we maybe decide on one.

### Publishing documentation

In order to make your content more discoverable for other users, you can place it in the documentation portion of the Talon HUD.  
For this, you need a documentation loader file, and a set of files to load in. An example of a documentation loader file that loads in a file inside of a folder as documentation can be seen below.  

```python
from talon import scope, app, actions
import os

# Get the absolute path to the documentation directory for your package
documentation_dir = str(os.path.dirname(os.path.abspath(__file__)))

def talon_hud_ready():
    # Check if Talon HUD is available to the user
    MINIMUM_TALON_HUD_RELEASE = 6
    if "user.talon_hud_available" in scope.get("tag") and \
        scope.get("user.talon_hud_version") != None and scope.get("user.talon_hud_version") >= MINIMUM_TALON_HUD_RELEASE:
        actions.user.hud_add_documentation("Example text", 
            "gives a short description of your available documentation.",
            documentation_dir + "/example.txt")

app.register("ready", talon_hud_ready)
```

When you are drafting documentation, it is advised to turn on the development mode of the Talon HUD, this will make the content reload as you update the documentation file.
Turn it on using `head up development start`, and when you are done again, turn it off with `head up development stop`.

### Publishing walkthroughs

Walkthroughs are a set by step guide through a process, that you can create yourself as well. Just like publishing documentation above, you need to set up a loader that can load in the walkthrough file into the HUD.
An example of a walkthrough loader that loads in a single .json file that expands upon the documentation loader above is given below.

```python
...
    MINIMUM_TALON_HUD_RELEASE = 6
    if "user.talon_hud_available" in scope.get("tag") and \
        scope.get("user.talon_hud_version") != None and scope.get("user.talon_hud_version") >= MINIMUM_TALON_HUD_RELEASE:
            # Media usage
            actions.user.hud_add_walkthrough("Example walkthrough", 
                documentation_dir + "/example walkthrough.json")

...
```

A walkthrough file can either be a .json file, which allows you to add contextual hints as well, or a markdown file, which does not have any context hints.

The .JSON file format is shown below, where the text 'Please turn on command mode' is shown if you do not have command mode turned on. The walkthrough also has a single voice command, `head up hide status bar`, inside of it.

```json
[
    {
	    "content": "This is an example walkthrough step! Say <cmd@head up hide status bar/> to continue!",
		"modes": ["command"],
		"tags": [],
		"context_hint": "Please turn on command mode"
	}
]
```

When you are designing walkthroughs, it is advised to turn on the development mode of the Talon HUD, this will make the content reload as you update the walkthrough file.
Turn it on using `head up development start`, and when you are done again, turn it off with `head up development stop`.

For more advanced usecases you can programmatically add a walkthrough as well with the actions `user.hud_create_walkthrough_step` and `user.hud_create_walkthrough` available in content/walkthrough.py.

### Markdown(.MD) support

Both for documentation and for walkthroughs, a subset of the markdown file format is supported.

The current support allows:
- Bolding
- Italizing
- Quoting with backticks

Notable things that aren't supported are:
- Headings
- Horizontal lines
- Links
- Images
- Advanced markdown ad ons like tables, flowcharts

The markdown file format is automatically detected when a file with .md is loaded in.

In walkthroughs, every new line starts a new walkthrough step.

## Non-text content

This is still being fleshed out, but in the mean time, you can take a look at the [previous content documentation](docs/deprecated_docs/CONTENT_README.md)

## Sticky content

TODO - Give a thorough explanation of the poller and topic system