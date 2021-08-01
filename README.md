# Unofficial Talon Head Up Display

This set of user scripts is meant to help build an awesome visual head up display elements using the Talon Canvas apis. 
It keeps your preferences saved in a CSV file, so that whenever you restart Talon, your HUD will be as you left it.
All the widgets are themeable, which means you can change the colours and images around as you see fit.
Buttons are mapped to actions as well, so you can change those to your wishes using .talon files as well.

# Setup

In order to use the HUD, it is best to set it up next to a version of [knausj_talon](https://github.com/knausj85/knausj_talon/) as it works out of the box. 
However, if you have a different user folder, you can look at the knausj_bindings.py and implement your own content updater.

# Widgets

The status bar

This widget will display the current Talon mode ( Command, dictation or sleep ) and will display the detected or forced language.
The default action of dwelling on the mode icon puts Talon in sleep mode after 1.5 seconds, and the close icon closes the HUD. 
The buttons can also be clicked to activate the dwell action immediately.

You can customize the status bar in multiple ways
- You can add the current natural languge by uncommenting line 42 from the display.py file
- You can change the functionality of the icons by changing the activate_statusbar_icon action in the widgets/statusbar.py file all the way at the bottom.
- You can add your own non-clickable icons to the statusbar as well, like in the example .talon file below

```
^Frikandel$: 
	user.add_status_icon("food", "nl_NL", "Dutch food")
^English breakfast$: 
	user.add_status_icon("food", "en_US", "English food")
^Doner kebab$: 
	user.add_status_icon("food", "de_DE", "German food")
^Croque madame$: 
	user.add_status_icon("food", "fr_FR", "French food")
^Pizza pepperoni$: 
	user.add_status_icon("food", "it_IT", "Italian food")
^Cheburek$: 
	user.add_status_icon("food", "ru_RU", "Russian food")
^Pierogi$: 
	user.add_status_icon("food", "pl_PL", "Polish food")
^Souflaki$: 
	user.add_status_icon("food", "el_GR", "Greek food")
^Churros$: 
	user.add_status_icon("food", "es_ES", "Spanish food")
^I am not hungry$: 
	user.remove_status_icon("food")
```

The event log

This widget works like the command history from knausj, but instead every message has a timed life of about 9 seconds before it disappears, keeping your screen free of clutter.
It isn't just limited to the command history however, you can append any message you want using the user.add_hud_log() action.
For example, adding this to your talon files adds a log to the event log widget

```
testing event log message:
	user.add_hud_log("event", "What I like to drink most is wine that belongs to others")
```

The ability bar

This widget is meant as a place for commands that continually shift in availability or in a timed manner.
It includes visualisations for 'cooldown' and 'channel' periods, much like you would see in an MMORPG. 
It also allows for control visualisation, briefly blinking bigger upon activation.

# Commands

All the commands of this repository can be found in commands.talon . A brief rundown of the commands is listed here:

`head up show` opens up the HUD as you left it
`head up hide` hides the complete HUD
`head up theme <themename>` switches the theme of all the widgets to the selected theme. Default themes are `light` and `dark` for light and dark mode respectively

You can also target individual widgets like the status bar and event log for hiding and showing. 
`head up show <widget name>` enables the chosen widget
`head up hide <widget name>` hides the chosen widget

By default, the widgets except for the status bar will hide when Talon goes in sleep mode, but you can keep them around, or hide them, with the following commands
`head up show <widget name> on sleep` keeps the chosen widget enabled during sleep mode
`head up hide <widget name> on sleep` hides the chosen widget when sleep mode is turned on

On top of being able to turn widgets on and off, you can configure their attributes to your liking.
Currently, you can change the size, position and font size

`head up drag <widget name>` starts dragging the widget
`head up resize <widget name>` starts resizing the widgets width and height
`head up expand <widget name>` changes the maximum size of the widget in case the content does not fit the regular width and height. 
By default these two dimensions are the same so the widget does not grow when more content is added
`head up text scale <widget name>` starts resizing the text in the widget
`head up drop` confirms and saves the changes of your changed widgets
`head up cancel` cancels the changes. Hiding a widget also discards of the current changes

Some widgets like the event log also allow you to change the text direction and alignment
`head up align <widget name> left` aligns the text and the widget to the left side of its bounds
`head up align <widget name> right` aligns the text and the widget to the right side of its bounds
`head up align <widget name> top` changes the direction in which content is placed upwards
`head up align <widget name> bottom` changes the direction in which content is placed downwards

If you prefer having a more basic animation free set up, or want to switch back to an animated display, you can use the following commands 
`head up basic <widget name>` disables animations on the chosen widget
`head up fancy <widget name>` enables animations on the chosen widget

# Updating content

As there only exists a single widget right now, the updating content flow is still in its infancy and is subject to change.
This section will be properly expanded when more widgets are added.

# Guidelines

The general idea of this repository is to seperate out three concepts, the users UI preferences, the content on display and the actual display logic.
These three silos are based on assumptions for three personas. The User, the Scripter and the Themer.

The **User** wants to have their content displayed in a way that matches their intentions. 
They decide where they want to place their widgets, what dimensions the widgets should have, what theme should be on display and what size the font should be. After all, the User might be colour blind or have a reduced field of vision. This repository aims to accomodate to them.
The User preferably doesn't have to change code when changing widgets around, and really doesn't want to lose their carefully crafted preferences or change their voice workflow around.

The **Scripter** wants to display their awesome creations in a visually appealing way without actually having to write out all the code required for that. They spent a bunch of time making an output that is useful, like an autocomplete feature or a command log, and they really don't want to spend more time fiddling around with canvas stuff.
The Scripter just sends their content over to the HUD, which knows where the user wants it and in what way.

The **Themer** wants to make an amazing visual experience happen, but do not really want to deal with the nitty gritty details of the widgets themselves. They want to change icons, colours and other visual properties of the UI themselves. And they do not like being limited, preferably having as much freedom of expression as possible.

These three personas are the spirit of this repository. As such, when new content is added to this repository, it should try to adhere to the needs and wishes above.

# Theming

If you want to add your own theme, simply copy and paste an existing theme folder over, give it a new name, define it in the commands.talon file and start changing values in the themes.csv file of your copied over directory.
In general, it is best to keep the images small for memory sake. But otherwise go nuts.

# Roadmap

These are ideas that I want to implement in no specific order and with no specific timeline in mind.

- WIP - An event log that can be filtered by the user, with a time to life setting that makes the message fade away ( much like a status message in an FPS )
- A regular text panel with a header and a close icon with limited growth bounds.
- A fallback text panel that shows every content update that isn't specifically registered by another text panel
- A context menu widget that can be opened by right clicking on a widget with mouse_enabled turned on.
- An indicator widget that follows the cursor around to show a single state that is important to the current task at hand
- An image panel with a header and a close icon which displays image content
- A capture that checks what themes are available on app ready by checking the directories in themes

- Multiscreen setups and how to best work with those, maybe with multiple preference files per monitor
- Multi-drag to drag every widget simultaniously

If any of these ideas seem cool for you to work on, give me a message on the talon slack so we can coordinate stuff.

# Acknowledgements

The icons used are taken from https://icons.getbootstrap.com/.

The language icons are made by https://www.freepik.com hosted on https://www.flaticon.com/.
If your language isn't in the themes, you can download icons for free with attribution of freepik.com and change their size to 35x35 before saving them as a .png file in your theme.