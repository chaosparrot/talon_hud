# Content publishing

You can publish all kinds of content to the various widgets of the HUD.

For example:
- Status bar icons to display a certain state
- Log messages
- Textual content with options to bold, slant or emphasise in a number of colours
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
- Type: What style we need to use to render the log. Currently supports 'event' for info styling, and 'command' for regular styling.
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
- Image: This is a path to an image. By default, the path 'talon_hud/themes/CURRENT_USER_THEME/IMAGE.png' is assumed if no .png is added. Currently, there is no support of adding images outside of the themes yet.

TODO - ADD SUPPORT FOR IMAGES OUTSIDE OF TALON_HUD DIRECTORY
TODO - ADD ICONS THAT ARE FUNCTIONAL LIKE THE MODE ICON

# Publishing to a text box

Publishing to a text box is done using the action hud_publish_content. A quick python example which claims a text box and shows the contents is shown below.

``` 
from talon import actions
actions.user.hud_publish_content('This is my content!')
```

These are the values that you can give to the hud_publish_content action
- Content: Content with rich text markers to display in the main body. Rich text markers are explained below.
- Topic: This is used to mark your content and will determine where or if your content gets shown.
- Title: This is the header title that will be shown in the text box. This value will also be used to address the text box. For example, if you set a title 'Command area', the user will be able to say 'Command area hide' to hide the text box.
- Show: This is a True or False value. If set to True, this will urge a widget to display and enable itself if it isn't shown yet. If the user has minimized the text box, it will not be opened. Defaults to True.
- Buttons: These are extra HudButton added to the context menu when the user right clicks the text box, or like in the example above, says 'command area options'.

# Rich text markers

In certain widgets like the text box, you can add rich text markers. These will apply styling to the text within them. Rich text needs to be opened with a style marker and closed with a closing marker.  
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

For simple usecases, like popping up a single piece of text, just being able to publish content is enough. However, sometimes you want to listen continuously for changes, like changing scopes or updating the list of recent commands.  
You can do your own event handling if you like, but the HUD also supports a concept called Pollers, some examples can be found in the talon_hud/content folder.

A poller is an object that registered to the Talon HUD, and will be enabled when the user requests it.  
On top of that, if the user changes content, or closes the Talon HUD, your poller will be automatically disabled and reenabled when neccesary, saving some clean up code on your end.  
In the future I also plan on re-enabling the poller when the user restarts Talon altogether, meaning that your users will not have to activate your content with a voice command with every restart.

Below is an example of a poller that increments a number by one every 200 milliseconds and posts it to a text box.

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
