Unofficial Talon Head Up Display
=====

![Overview image](/docs/intro.png)

This set of user scripts is meant to help build an awesome visual head up display elements using the Talon Canvas apis.  
It keeps your preferences saved in CSV files, so that whenever you restart Talon, your HUD will be as you left it.  
All the widgets are themeable, which means you can change the colours and images around as you see fit.

Setup
----

In order to use the HUD, it is best to set it up next to a version of [knausj_talon](https://github.com/knausj85/knausj_talon/) as it works out of the box. 

Widgets
----

### 1. Status bar

This widget will display the current Talon mode ( Command, dictation or sleep ) and will display the detected or forced language. The default action of dwelling on the mode icon puts Talon in sleep mode after 1.5 seconds, and the close icon closes the HUD.  
The buttons can also be clicked to activate the dwell action immediately.  

You can customize the status bar in multiple ways
- You can add the current natural language by uncommenting line 96 from the display.py file
- You can add the microphone toggle by uncommenting line 100 from the display.py file
- You can change the functionality of the icons by changing the activate_statusbar_icon action in the widgets/statusbar.py file all the way at the bottom.

### 2. Event log

This widget works like the command history from knausj, but instead every message has a timed life of about 9 seconds before it disappears, keeping your screen free of clutter. It isn't just limited to the command history however, you can add your own messages as well.

### 3. Text box

A catch all-widget for rich text display. It stretches the content until the defined screen limits given by the user. It allows text in a variety of styles, including bold and italic, and various colours.  
The header contains the name of the panel, including a minimize and a close button. If the content is larger than the allotted screen space, it will create multiple pages which are navigable using a next and previous page button.  
The text box will align itself based on the given expansion limits. If more space is available to the left, it will align itself to the right, and so on.  

By default there is only one text box, but you can define multiple and assign them to specific commands in the display.py file. In the future this functionality will probably move to voice commands instead.

### 4. Choice panel

This widget shows choices that can be activated with either a mouse click or voice commands.  
The voice commands follow the simple principle of 'What you see is what you read', meaning that if a button says '2. Test choice' you can either say `option two` or `test choice` to activate it.  
The widget allows for a short explanation before the choices, and the choices can be defined with either single or multiple selection. With preselected choices also definable.  
By default there is only one choice panel available, this is to make sure you don't get overloaded with choices on your screen.

### 5. Context menu

A context menu can be configured to open on any widget that has mouse clicks enabled.  
This widget contains a bunch of buttons that will interact with the widget that it has opened.  
The context menu will attempt to stay on the screen where the right-click was made, and as such will change position accordingly.

### 6. Walkthrough panel

This widget is meant to guide users through a predefined workflow to familiarize them with it.
You can use this to give an interactive experience for users to learn the ins and outs of various workflows.
Included in the Talon HUD is a simple walkthrough for using the Talon HUD itself, but any package can make walkthroughs or workflows.

### 7. Ability bar

Much like the status bar, except it only allows you to show icons and can be displayed independently of the status bar.  
By default, it does not have any visual indication, but I have used it in some of my personal scripts to show movement directions.  

### 8. Cursor tracker

This widget follows your given pointer around and can display an icon or a colour near it.  
This can be used for example to show the status of a specific thing near your eyetracking gaze through your mouse cursor.  
By default, there are no cursor indicators, they need to be programmed in using the content documentation.  

### 9. Screen overlay

This widget can annotate regions of the screen with text, icons and colours.
You can use it to show different regions for virtual keyboard usage combined with noises for example.

Voice commands
---

### General usage

All the commands to change widgets around can be found in commands.talon. A brief rundown of the commands is listed here:

`head up show` opens up the HUD as you left it.  
`head up hide` hides the complete HUD.  
`head up theme <themename>` switches the theme of all the widgets to the selected theme. Default themes are `light` and `dark` for light and dark mode respectively.  

You can also target individual widgets for hiding and showing.  
`head up show <widget name>` or `<widget name> show` enables the chosen widget.  
`head up hide <widget name>` or `<widget name> hide` hides the chosen widget.  
`<widget name> minimize` minimizes the widget if it is supported for the widget.  
`<widget name> maximize` reopens the widget if it is supported for the widget.  

Widgets can have extra options as well.  
`<widget name> options` shows them on screen. Simply saying the text inside the buttons that appear will activate the button, of course you can also just click them as well.

Some widgets like the text box allow you to go to a next or previous page.  
`<widget name> next` moves to the next page of the content if exists. You can use repeaters with this, so `<widget name> next twice` will go forward twice.  
`<widget name> previous` or `<widget name> back` goes to the previous page if it exists.

### Widget setup

By default, the widgets except for the status bar will hide when Talon goes in sleep mode, but you can keep them around, or hide them, with the following commands.  
`head up show <widget name> on sleep` keeps the chosen widget enabled during sleep mode.  
`head up hide <widget name> on sleep` hides the chosen widget when sleep mode is turned on.

On top of being able to turn widgets on and off, you can configure their attributes to your liking.  
Currently, you can change the size, position, alignment, animation and font size.  

`head up drag <widget name>` starts dragging the widget. You can also drag multiple widgets at the same time with `head up drag <widget names>`.
`head up resize <widget name>` starts resizing the widgets width and height.  
`head up expand <widget name>` changes the maximum size of the widget in case the content does not fit the regular width and height.  
By default these two dimensions are the same so the widget does not grow when more content is added.  
`head up text scale <widget name>` starts resizing the text in the widget.  
`head up drop` confirms and saves the changes of your changed widgets.  
`head up cancel` cancels the changes. Hiding a widget also discards of the current changes.

Some widgets like the event log also allow you to change the text direction and alignment  
`head up align <widget name> left` aligns the text and the widget to the left side of its bounds.  
`head up align <widget name> right` aligns the text and the widget to the right side of its bounds.  
`head up align <widget name> top` changes the direction in which content is placed upwards.  
`head up align <widget name> bottom` changes the direction in which content is placed downwards.

If you prefer having a more basic animation free set up, or want to switch back to an animated display, you can use the following commands  
`head up basic <widget name>` disables animations on the chosen widget.  
`head up fancy <widget name>` enables animations on the chosen widget.

You can have different positions on different monitor configurations, this happens automatically when you add more monitors.

Each widget position is saved in a monitor preferences file in your preferences folder.  
Every time you attach a different monitor, or use a different screen size, a specific monitor preferences file will be used.
If your monitor changes during use, Talon HUD will attempt to rebuild your configured widget positions on your main monitor.  
But this isn't 100% foolproof, so you might have to drag and configure some widgets around.  

All the non-position related settings are saved in the widget_settings.csv file in your preferences folder.

Using Talon HUD in your own packages
---

The HUD provides a bunch of hubs like documentation and walkthroughs that you can leverage in your own packages.
That way, if a user has the Talon HUD together with your own package, you can provide documentation and other niceties without having to worry about making your own user interfaces.
Visit the [package enhancement documentation](docs/README.md) for more information.

Updating widgets with content
---

If you want to add your own content to the widgets, visit the [content publishing documentation](content/README.md)

Theming
---

If you want to add your own theme, simply copy and paste an existing theme folder over, give it a new name, define it in the commands.talon file and start changing values in the themes.csv file of your copied over directory.  
In general, it is best to keep the images small for memory sake. But otherwise go nuts.

There are some values that have special settings, like event_log_ttl_duration_seconds, which can be set to -1 to have the logs stay without disappearing.
As there is not a lot of theming going around, it is best to ask me on the Talon slack if you have questions about them.

Context aware Talon HUD environments
---

You can change your HUD layout entirely using the context management of Talon.  
Let's say you want to change the placement and enabled widgets when you enter a browser.  
This is entirely achievable using the 'user.talon_hud_environment' setting.  

We implement this in the following talon_hud_browser.talon file example.  
When you focus a browser after adding a talon file like this, it will automatically make a new set of preference files specifically for the 'browser_hud' Talon HUD environment.
You can then change your HUD around as you see fit. When you switch out of your browser context, it will change the HUD back as you left it before opening the browser.
And next time you open up the browser again, it will neatly place the widgets where they were left previously in the 'browser_hud' environment.

```
tag: user.talon_hud_visible
and tag: browser
-
settings():
    user.talon_hud_environment = "browser_hud"
```

Changing the preferences folder
---
You can change the folder in which your HUD preferences are saved by going to the preferences.py file and following the instructions at the top of the file.

Development guidelines
----

The general idea of this repository is to seperate out three concepts, the users UI preferences, the content on display and the actual display logic.  
These three silos are based on assumptions for three personas. The User, the Scripter and the Themer.

The **User** wants to have their content displayed in a way that matches their intentions.  
They decide where they want to place their widgets, what dimensions the widgets should have, what theme should be on display and what size the font should be. After all, the User might be colour blind or have a reduced field of vision. This repository aims to accomodate to them.  
The User preferably doesn't have to change code when changing widgets around, and really doesn't want to lose their carefully crafted preferences or change their voice workflow around.

The **Scripter** wants to display their awesome creations in a visually appealing way without actually having to write out all the code required for that. They spent a bunch of time making an output that is useful, like an autocomplete feature or a command log, and they really don't want to spend more time fiddling around with canvas stuff.  
The Scripter just sends their content over to the HUD, which knows where the user wants it and in what way.

The **Themer** wants to make an amazing visual experience happen, but do not really want to deal with the nitty gritty details of the widgets themselves. They want to change icons, colours and other visual properties of the UI themselves. And they do not like being limited, preferably having as much freedom of expression as possible.  

These three personas are the spirit of this repository. As such, when new content is added to this repository, it should try to adhere to the needs and wishes above.

**Voice command guidelines**

This repository tries to adhere to "What you see is what you say". If there is a widget with a header title, we make sure the widget can be addressed with that header name.  
Likewise, if there is a button on display on the screen, just reading the text on the button should activate it.  
If these options aren't available, documentation must be supplied with easily parseable voice commands so the users workflow is impacted minimally by reading large swats of text.

Roadmap
---

These are ideas that I want to implement in no specific order and with no specific timeline in mind.

- An image panel with a header and a close icon which displays image content
- Improved theming experience and more styling options
- Splitting out or merging topics from widgets into separate widgets
- Better default image, dimension and font scaling based on physical dimensions of the screen

Known issues
---
- Multiple page walkthrough panel does not work properly with text indices

If any of these ideas seem cool for you to work on, give me a message on the talon slack so we can coordinate stuff.

Acknowledgements
---

The icons used are taken from https://icons.getbootstrap.com/.  
Some of the icons like the copy icon are taken from fontawesome.

The language icons are made by https://www.freepik.com hosted on https://www.flaticon.com/.  
If your language isn't in the themes, you can download icons for free with attribution of freepik.com and change their size to 35x35 before saving them as a .png file in your theme.
