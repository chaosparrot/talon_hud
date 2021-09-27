# Content publishing

You can publish all kinds of content to the various widgets of the HUD.

For example:
- Status bar icons to display a certain state
- Log messages
- Textual content with options to bold, slant or emphasize in a number of colours
- Context menu options for various widgets

Publishing content to head up display can be done using actions found in content/state.py.

Below are specifics explained per widget

# Publishing events to the log

By default, the event log above your status bar shows the voice commands being recognized. However, you can add your own logs as well.

``` 
from talon import actions
actions.user.hud_add_log('command', 'This is a log message!')
```
The following values can be added to hud_add_log
- Type: What style we need to use to render the log. 
  Currently supports 'command' for regular styling, 'success', 'warning' and 'error' for various validation messages, and 'event' for notices.
- Message: The log message to display

# Publishing icons to the status bar

The status bar is the main widget which displays what mode the user is currently in and a number of other elements like used language that should be shown at a glance.  
You can add your own status icons that will display an image that you have given next to the main mode icon.

``` 
from talon import actions
actions.user.hud_add_status_icon('my_status_icon', 'dictation_icon.png')
actions.user.hud_remove_status_icon('my_status_icon')
```

These are the values that you can give to hud_add_status_icon:
- Identifier: This is a value that uniquely identifies your icon. You can use this to later remove the icon using hud_remove_status_icon
- Image: This is a path to an image. By default, the path 'talon_hud/themes/CURRENT_USER_THEME/IMAGE.png' is assumed if no .png is added. 
However, you can use any path on the system to display an image. 
If you are shipping a seperate repository, I recommend making the path relative to the directory where you are running your code from
As that makes no assumptions how the user has built up their talon_user folder.
Something like this:
```
from talon import actions
import os
my_file_dir = os.path.dirname(os.path.abspath(__file__))
icon = my_file_dir + '/image.png'
actions.user.hud_add_status_icon('my_status_icon', icon)
```

TODO - ADD ICONS THAT ARE FUNCTIONAL LIKE THE MODE ICON

# Publishing to a text panel

Publishing to a text panel is done using the action hud_publish_content. A quick python example which claims a text panel and shows the contents is shown below.

``` 
from talon import actions
actions.user.hud_publish_content("This is my content!")
```

These are the values that you can give to the hud_publish_content action
- Content: Content with rich text markers to display in the main body. Rich text markers are explained below.
- Topic: This is used to mark your content and will determine where or if your content gets shown.
- Title: This is the header title that will be shown in the text panel. This value will also be used to address the text panel. For example, if you set a title 'Command area', the user will be able to say 'Command area hide' to hide the text panel.
- Show: This is a True or False value. If set to True, this will urge a widget to display and enable itself if it isn't shown yet. If the user has minimized the text panel, it will not be opened. Defaults to True.
- Buttons: These are extra HudButton added to the context menu when the user right clicks the text panel, or like in the example above, says `command area options`.
- Tags: Tags to be enabled while this content is visible on the screen. You can use this to add exploratory voice commands embedded in your text.

# Adding right click buttons to a text panel

You can add right click menus to text paneles and other widgets as well that can be opened using the `<widget name> options` command.
These menus contain a few default options like closing the panel and copying the contents, but you can also add your own buttons. These are given as an extra parameter in the hud_publish_content action.

Let's say we want to add a button to our content that prints to the debug log. What we do is the following:

```
from talon import actions

button = actions.user.hud_create_button("Print to console", print)
buttons = [button]

actions.user.hud_publish_content("Text with content", "test", "Test content", True, buttons)
```
Now when the content is published, and extra button can be found in the widgets right click menu. Like the other options in it, when it is shown, the text inside the button is used to activate it, in this case, print to console!
Users can also get accusomed to the option, as it is also available as a quick option. Saying `test content print to console` will activate the button even though the context menu hasn't shown up yet.

# Offering choices and options

For displaying options to the user, you can publish content with choices to the 'choice' topic. The choices attached to this topic will be shown on the screen as buttons for the user to click or to say.
There are two steps to defining the choices. First, create the choices using the hud_create_choices action. This takes in a list of objects, the function to call when a selection is made, and whether or not we are dealing with multiple or single choice.

For example:
```
from talon import actions
choices = actions.user.hud_create_choices([{"text": "Sugar", "image": "next_icon", "selected": True},{"text": "Milk"},{"text": "Nothing"},{"text": "Sweetener"}, {"text": "Nails"}], print, False)
``` 

This line will create a list where there are five choices with the text sugar, milk, nothing, sweetener and nails in that order. Where the first option Sugar is preselected. Only one option can be selected.

You can define two things in the choice list, namely: 
- text: The text to display in the choice. Also used for the voice command to activate it.
- image: This is a path to an image. By default, the path 'talon_hud/themes/CURRENT_USER_THEME/IMAGE.png' is assumed if no .png is added. Currently, there is no support of adding images outside of the themes yet.
- selected: Whether or not the choice is preselected

These are the values that you can give to the hud_publish_choices action
- Choices: The choice list explained above
- Callback: A defined function to call when the choices have been selected
- Multiple: True or False - Whether or not the user has to select multiple choices or just one. Defaults to just one.

Now that you have your choices, you will have to publish them using the hud_publish_choices action.

```
actions.user.hud_publish_choices(choices)
```

These are the values that you can give to the hud_publish_choices action
- Choices: A HudChoices object created using the hud_create_choices action.
- Title: The title of the choice component. Defaults to 'Choices'.
- Content: The rich text content explanation. Defaults to an explanation about using the option command. 

Published choices will always open the choice panel up when they are updated.

If you want to make multi-level menus ( selections that open up a new choice widget ), you can make the selection function return True. 
This way it will not automatically close the choice panel upon selection.

# Rich text markers

In certain widgets like the text panel, you can add rich text markers. These will apply styling to the text within them. Rich text needs to be opened with a style marker and closed with a closing marker.  
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
- /> : Closing marking - ends the latest style applied

When writing rich text containing voice commands, make sure to emphasise the voice commands with one of these markers so they stand out from the rest of the text.  
This makes it easier for the user to quickly pick out the voice commands from the text you have writen.  
There isn't a firm styling for voice commands yet, so for now just apply a bold marker at the minimum until we maybe decide on one.

# Polling / continuously updating content

For simple use cases, like popping up a single piece of text, just being able to publish content is enough. However, sometimes you want to listen continuously for changes, like changing scopes or updating the list of recent commands.  
You can do your own event handling if you like, but the HUD also supports a concept called Pollers, some examples can be found in the talon_hud/content folder.

A poller is an object that registered to the Talon HUD, and will be enabled when the user requests it.  
On top of that, if the user changes content, or closes the Talon HUD, your poller will be automatically disabled and reenabled when neccesary, saving some clean up code on your end.  
In the future I also plan on re-enabling the poller when the user restarts Talon altogether, meaning that your users will not have to activate your content with a voice command with every restart.

Below is an example of a poller that increments a number by one every 200 milliseconds and posts it to a text panel.

``` 
from talon import actions, Module, app, cron

class PollerExample:
    enabled = False
    job = None
    count = 0

    def enable(self):
        if self.job is None:
            self.update_content(True) # Updates the content and requests the HUD to show the widget if it is disabled
            self.job = cron.interval('200ms', self.update_content)
        print("ENABLING EXAMPLE POLLER")
                
    def disable(self):
        # Clean up code goes here
        cron.cancel(self.job)
        self.count = 0 
        self.job = None
        print("DISABLING EXAMPLE POLLER")        

    # Updates the content of a widget using hud_publish_content
    def update_content(self, show=False):
        self.count += 1
        actions.user.hud_publish_content('Update count: ' + str(self.count), 'example', 'Poller example', show)


# Registers the poller when talon is finished loading
def append_poller():
    actions.user.hud_add_poller('example', PollerExample())
app.register('ready', append_poller)

mod = Module()
@mod.action_class
class Actions:

	def example_poller():
		"""Activate the example poller"""
		print("ACTIVATE EXAMPLE POLLER!")
		actions.user.hud_activate_poller('example') # Activates the example poller if this action is activated ( through a voice command for example )
```

If you add this in a talon file, you can test it for yourself when saying **test example poller**:

```
test example poller: user.example_poller()
```
