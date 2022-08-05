Unofficial Talon Head Up Display
=====

![Overview image](/docs/intro.png)

The HUD is a user interface that helps improve your workflow. Inspired by gaming HUDs, it is meant to show just the right amount of info to your screen without getting in the way of your actual work. It is resizable, scalable and placable in whatever combination you can come up with, so only the screen space that you allow will be used, just as you left it.  

It combines voice commands with clickable buttons, allowing for seemless transitions between using your regular old controls and your voice command flow.  
It also has keyboard navigation enabled, so you can navigate the widgets using your keyboard shortcuts instead.

On top of that, the HUD remembers where you left off. It keeps the widgets in the place you have left them for the next time you start up, and when you add or remove monitors, it will remember where you kept the widgets in those instances.  
This makes the HUD excellent for switching between a single laptop screen, and connecting a monitor in the office or at home.

By default, the HUD comes in a light and a dark mode, but you can create other themes yourself as well!

## Table of contents
1. [Installation and fixing](#installation)
2. [Important voice commands](#important-voice-commands)
3. [Available content](#available-content)
    1. [Talon mode tracking](#talon-mode-tracking--turned-on-by-default-)
    2. [Speech history](#speech-history--turned-on-by-default-)
    3. [Microphone muting and management](#microphone-management)
	4. [Language tracking](#language-tracking)
	5. [Programming language tracking](#programming-language-tracking)
	6. [Focus tracking](#focus-tracking)
	7. [Documentation](#documentation)
	8. [Walkthroughs](#walkthroughs)
	9. [Debugging](#debugging)
	10. [Audio feedback](#audio-feedback)
3. [Accessibility features](#accessibility-features)
	1. [Keyboard controls](#keyboard-controls)
	2. [Audio cues](#audio-cues)
	3. [Screen reader usage](#screen-reader-usage)	
4. [Customizing the HUD](#customizing-the-hud)
	1. [Hiding and showing widgets](#hiding-and-showing-widgets)
	2. [Repositioning widgets](#repositioning-widgets)	
    3. [Changing the size of text and widgets](#changing-the-size-of-text-and-widgets)
	4. [Changing alignment of widgets](#changing-alignment-of-widgets)
	5. [Animations](#animations)
	6. [List of available widgets](#list-of-available-widgets)
5. [Advanced usage](#advanced-usage)
    1. [Changing appearance and audio](APPEARANCE.md)
	2. [Preferences folder](#preferences-folder)
	4. [Talon HUD environments](#talon-hud-environments)
	5. [Text content, documentation and walkthrough creation](CUSTOMIZATION.md#creating-text-content)
	6. [Non-text content creation](CUSTOMIZATION.md#non-text-content)
	7. [Sticky content creation](CUSTOMIZATION.md#sticky-content)
6. [Miscellaneous](#miscellaneous)
    1. [Roadmap](#roadmap)
	2. [Development philosophy and guidelines](#development-philosophy-and-guidelines)
	3. [Acknowledgements](#acknowledgements)

## Installation

To use the Talon HUD, you need to have Talon Voice installed on your computer.
On top of that, it is best to set it up next to a version of [knausj_talon](https://github.com/knausj85/knausj_talon/) as it gives you a lot of other voice commands to work with.  
The only thing you need to do is click the 'Code' button on top of this page, download the zip and extract it inside of your Talon user folder somewhere.
After that, it should start up right away if you have Talon set up, or on your next Talon start up. A walkthrough will lead you through the next steps.

If for some reason the HUD seems broken, you can try and see if clearing out the preferences folder helps, as that is where all your personal settings are stored.

## Important voice commands

`head up show` turns on the head up display.  
`head up hide` hides the head up display.  
`toolkit options` shows all the available content connected to the HUD toolkit, the options on the screen can be read out for navigation.  
`head up theme dark` and `head up theme light` switch in between the default available themes.
`head up audio enable` enables the audio cues.
`head up mute` mutes the audio cues.

All voice commands are available in the .talon files inside of the HUD, while some are also generated based on the titles of the widgets themselves.

## Available content

### Talon Mode tracking ( turned on by default )

Talon comes in a variety of modes, like the command mode in which you utter commands, or the sleep mode where no commands are used but the wake word. To keep track of what mode you are currently in, the Talon HUD offers a status bar icon that can be clicked. 
This is added by default, and when clicked, turns Talon either in sleep mode, or from sleep mode back to your previous mode, be it command or dictation mode.  
Removing the mode icon is possible as well to keep a more minimal look, by saying `status bar remove mode indicator` or by right clicking the status bar and clicking 'Remove mode indicator'.  
The status bar will always show whether you are in sleep mode or not at a glance, regardless of when you have mode icon added or not, by changing the appearance of the status bar itself.  

You can change the mode detection, toggle and available modes yourself as well, if your set up requires a more personal touch. To see how, read the link below.

[Customizing mode tracking](CUSTOMIZATION.md#customizing-mode-tracking)

### Speech history ( turned on by default )

Taking inspiration from FPS games, the event log widget allows you to read back voice commands as you make them, as well as clearing themselves up after a few seconds to give you back that screen space.  
Different options to show commands are available. You can keep the commands visible indefinitely, or temporarily freeze them to discuss them, perfect for pairing sessions.  
All of these options can be shown and toggled by saying `event log options`.

If you need are more in-depth view of the commands said, you can say `toolkit speech` or navigate from the status bar with Content toolkit -> Debugging -> Speech to find a full overview of the commands said, as well as the used engine and microphone.

### Microphone management

In some scenario's like conference calls, it is handy to have a way to instantly turn off the microphones input to Talon. This toggle can be placed on the status bar by saying `status bar add microphone` or right clicking on the status bar and selecting 'Add microphone'.  
Switching the microphone off this way prevents accidental wake messages or commands from triggering functionality while you are talking to your friends or colleges.

On top of that, you can also switch microphones on the fly by saying `toolkit microphones`, or right clicking the status bar and following Content toolkit -> Microphones. The microphone selected here will be used as a favorite setting, so if you toggle the microphone on and off, it will remember the selected microphone here and switch back to that microphone.  
This comes in handy when you have multiple microphone set ups, like a laptop microphone and an on desk microphone.

### Language tracking

For the multilingual folks out there, switching between different languages for dictation is a necessity to keep your workflow working with voice. For that purpose, you can add a language icon indicating your language on the status bar by saying `status bar add language` or right clicking the status bar to the option Add language.  

[Customizing languages](CUSTOMIZATION.md#customizing-language-tracking)

### Programming language tracking

A lot of programmers inhabit the Talon Voice community, and with them come many different programming languages. With those programming languages come different commands, and usually these are kept track of by the file extension available in a program, or by manually forcing a certain language to be used.  
To make sure you know what programming language context you are in, you can add a language icon to your status bar by saying `status bar add code language` or right clicking the status bar and clicking 'Add code language'.  
You can add and remove programming languages icons yourself, by following the instructions below.  

[Customizing programming languages](CUSTOMIZATION.md#customizing-programming-languages)

### Focus tracking

When returning back to your computer after a while, it can be hard to see what window Talon has focused for voice commands. This only gets harder if you have multiple monitors. To alleviate this problem, you can add a focus indicator to your status bar by saying `status bar add focus indicator` or right clicking the status bar and selecting 'Add focus indicator'.  
This will present an orange-red box on the top center of the currently focused window, to remind you what direction you're talking to.

### Documentation

Inside the HUD, there is a place where you can read out available documentation for certain voice commands, like a refresher of sorts. It is available if you say `toolkit documentation` or by navigating from right click menu in the status bar with Content toolkit -> documentation, there you will find a bunch of text that is published to the HUD. Simply say one of the titles on the screen to navigate to that content.  
You can also publish your own files to the HUD documentation, to keep as a reminder, or to enhance your own packages.

When you need to switch between pages, you can say `<widget name> next` or `<widget name> back` to go forward or backward in the current content.

You can read about creating your own content at [publishing documentation](CUSTOMIZATION.md#publishing-documentation)

### Walkthroughs

While having a good overview of all voice commands can be good, it is often overwhelming. To make the learning process a little less steep, the HUD offers some walkthroughs which guide you through voice commands one by one in a designed fashion, giving explanations about the voice commands as you go. You can find the walkthroughs by navigating through the status bar right click menu Content toolkit -> Walkthroughs or by saying `toolkit walkthroughs` instead.  
You can also create walkthroughs for your own work flow, or for your own packages as well. You can read about how to create walkthroughs yourself at [publishing walkthroughs](CUSTOMIZATION.md#publishing-walkthroughs)

### Debugging

When you are working with, or working on, your Talon scripts, it is often hard to see what is going on in the background. In order to give a slight peek inside of the current state of your Talon set up, there is a debugging menu that can be reached with the voice command `toolkit debugging`.

- The scope debugging option allows you to see the current app and title, the current tags and the current modes, and updates the content as they change.
- The speech debugging option allows you to see all recognized commands and their used time, with their used engine and microphone, so you can track down why recognition might have changed.
- The list debugging option gives you a look inside a single list as it changes.

### Audio feedback

While using Talon, it is possible to have some audio feedback while doing your commands. Things like knowing when talon goes to sleep or another mode, when the microphone is disconnected can all be enabled to have an audio trigger.
Not only that, you can enable syllable cues as well, which pronounce the syllables recognized in beeps. You can use this to distinguish between commands without looking at the screen.

## Accessibility features

The HUD aims to make your voice workflows accessible. From the get-go it has a focus on offloading things you need to remember into the visual spectrum. As time went on, things like theming, resizability and clicking were added as well, keeping up with the trend of making sure as many people could use the HUD as possible. 

However I did not originally take into account people with low-vision, or people who use screen readers and keyboards rather than mice or eyetrackers to do their daily computing. To help those people find a place in the Talon voice community as well, I've begun adding features to accommodate. 

### Keyboard controls

When you focus the Talon HUD, by clicking a widget or by saying `head up focus` or `focus head up`, you can start using keyboard controls. The HUD sort of works like tab bar, where you can navigate between the widgets using the **left and right arrow keys**, tab through content and space to activate or click elements. Unfocusing works using the **ESC** key, as if you had an overlay or a modal opened up. You can also say `head up blur` to unfocus the HUD.

You can also enable auto focus. Auto focus focuses the HUD element that has just changed by a voice command, so you can immediately start navigating it with your keyboard. This can be activated with `head up auto focus` and disabled using `head up disable auto focus`

There are also keyboard shortcuts to toggle focus on the HUD as well, by default this is **Alt-Shift-End**, but you can change it inside of keys.talon. I personally have a large keyboard with a numpad on the side, so I tend to bind focusing to the **divide** key, or key(keypad_divide) inside of .talon files.

These are all the currently available keyboard controls:
- **Tab and Shift-Tab**: Changes the focus of the available content in the widget and loops back around. The focus is shown as a border around the content.
- **Space**: This activates the currently focused element.
- **Left and right arrow keys**: When the main widget element is focused, this switches between the active widgets.
- **Up and down arrow keys**: Inside choice and context menus, this navigates between the available choices. There is no looping back to the first element. 
- **Page up and page down**: When a text widget or choice widget is focused, this moves between the available pages of the current content.
- **Escape**: Unfocuses the current element, either by going up to the main widget element, or out of the HUD entirely.
- **Enter**: Actives the current selection, but inside a choice widget with multiple choices, submits all the selected choices instead.

### Audio cues

Tunable auditory feedback has been added for a number of events, like mode changing and microphone changing, as well as focus changing, error notifications and voice command feedback.
All of these audio cues are grouped and their volume can be tuned individually or as a group.
To have a look at all the available audio cues and their enabled state and volume, you can say `toolkit audio`.

You can enable audio by saying `head up audio enable`, and you can change the volume of the audio by saying `head up audio volume <number between 0 and 100>`. By default the volume is set at 75.

You can refer to a specific group or cue by saying `head up audio <cue or group>`. You can for instance enable the interface cues with `head up audio interface enable`. And you can change its volume with `head up audio interface volume <number between 0 and 100>`

By default, the following things will be announced if audio is enabled:
- Command, dictation and sleep mode
- Microphone disconnected or disabled

Currently you can enable these audio cues as well:

- Interface cues: You can enable these with `head up audio enable interface`
    - Audio cue when focus in the HUD is changed
	- 'Bonk' cues when the end of content is reached
	- Error and notify cues when an error or notification is shown

- Syllable cues: You can enable these with `head up audio enable syllables`.
These turn your activated voice commands into beeps relating to the said syllables with pauses in between words. There are five pitches that are used:
    - High: For example 'Five' and 'near'
	- Mid high: For example 'went', 'cat', 'hair', 'space' and 'joy'
	- Mid: For example 'rob', 'sit', 'car', 'jaw', 'robe' and 'gown'
	- Low mid: For example 'bird', 'burn', 'fun' and the last syllable in 'open'
	- Low: For example 'could', 'boot' and 'queue'

For the syllable cues, you can also change when they become active. To learn more, check out the [Customizing syllable cues](CUSTOMIZATION.md#customizing-syllable-cues) page.

### Screen reader usage

Work is underway to make the HUD properly usable for screen reader users. Most of the ground work like an accessibility tree has been made, and I have done tests with some scripts to make the focused text be announced, but this is currently being developed.  
Expect this to be more fleshed out in the next version while I toy around with screen reader usability in combination with Talon as well.

## Customizing the HUD

While the base set up for the HUD is meant to be a good starting point, you will most likely want to tweak everything to fit your own unique needs. Below is a list of all the available changes you can make to widgets. For the explanations below, the <widget name> part is used to reference to the widget name that you want to change, in the last paragraph of this chapter is a list of available widgets and their names.

Some widgets can have alternative names too, which are the titles shown on top of them. In the case of a text box being titled 'Toolkit Options', you can say `toolkit options hide` to hide it.

### Hiding and showing widgets

You can hide specific widgets by saying `head up hide <widget name>`. Some content, like text that gets published, might still make that widget show up again, but you can also manually show the widget by saying `head up show <widget name>`.  
You can also use the widget shorthand, which is `<widget name> hide` and `<widget name> show`. 

### Repositioning widgets

Changing widgets' position can be done either by dragging them around the screen, or by saying `head up drag <widget name>`, confirming the position with `head up drop` or canceling it with `head up cancel`.  
If you want to change multiple widgets at the same time, you can say `head up drag <widget name one> <widget name two>`, and they will be moved simultaneously.

For some specific widgets like the cursor tracker where the position depends on the mouse cursor itself, saying `head up drag cursor tracker` will keep the widget in place, so you can change the position relative to the mouse cursor itself.

### Changing the size of text and widgets

Changing the font size of a widget to make the text more readable is done using the command `head up text scale <widget name>` and by dragging the mouse around. You can confirm the changes by saying `head up confirm` or cancel the changes by saying `head up cancel`.  

Widgets have two kinds of sizes, their minimal size, and their maximum growable size.

You can also change the minimal size that certain widgets take on by saying `head up resize <widget name>`, confirming it with `head up confirm` or canceling it with `head up cancel`. Note that changing the minimal size also resets the maximum growable size. And for some widgets, changing the size can also change the alignment of the content itself, as it is calculated using the two top points of the minimum and maximum growable size.

To change the maximum growable size of a widget, hold your mouse in the direction from the widget where you want it to grow, and say `head up expand <widget name>`, with the same confirmation and cancelation commands as the other commands.

Some widgets also have a more collapsed, minimized state, which you can activate by saying `head up minimize <widget name>` or `<widget name> minimize`. You can undo the minimization by saying `head up mazimize <widget name>` or `<widget name> maximize`.    

### Changing alignment of widgets

You can change the alignment of widgets by saying `head up align <widget name> <alignment>` where the alignment can be anything from `top`, `bottom`, `left`, `right` or in some widgets `center`. The alignment might also be connected to the minimal and maximal growth size as explained above as well.  

###	Animations

Most of the Talon HUD widgets have animations turned on by default, but you might not like those animations yourself. You can turn them off by saying `head up basic <widget name>`, or turn them back on by saying `head up fancy <widget name>`.

### List of available widgets

![Image showing the names of all the widgets next to them](/docs/widget_overview.png)

(*) The name of these widgets may change based on the title of the panel.

- Status bar: The bar on the bottom right of the screen with clickable icons.
- Event log: The log that is shown above the status bar showing all the commands.
- Text panel*: The text panel on the top right part of the screen.
- Choices*: The choice panel that is shown in the center of the screen.
- Documentation*: The documentation panel on the left.
- Walkthrough: The documentation panel on the left.
- Ability bar: An optional bar left of the status bar containing non-clickable icons.
- Screen overlay: A widget that can put labels all over the screen. Only used in the focus tracker so far.
- Cursor tracker: A widget that follows your mouse around. Currently has no available content.
- Context menu: The right click menu of a widget.

## Advanced usage

You can tweak more about the HUD and use it in more advanced ways if you feel like tinkering around.
For changing the appearance of the HUD, you can take a look at the [Changing appearance and audio](APPEARANCE.md) page.  
For customizing and creating your own content, you can have a look at the [Customization](CUSTOMIZATION.md) page.

### Preferences folder

The 'preferences' folder inside of the HUD contains all the changes the user has made to the HUD. All the files inside are non-critical, meaning that you can remove them and they will be regenerated based on the default settings when you next start up Talon.  
The user preferences are split into two files, the monitor file which contains all the positional information based on the current monitor set up, and the widget_settings.csv file, which contains all the non-positional information like widget enabled status, alignment and attached content.  
If you have another talon hud environment ( explained below ), you will have more files in the preferences folder as well, prefixed by the talon hud environment. These files are used purely for that environment.  

On top of widget related settings, the preferences folder can also contain files that are used for the content creation. An example of this is the programming_languages.csv file which contains available programming languages, the walkthrough.csv file which keeps track of all finished walkthroughs, and the hud_preferred_microphone.txt file, which contains the prefered microphone to toggle to with the status bar microphone toggle.  

If you want to customize the place where you keep your preferences, so you can bundle them all in one place for example, you can change the `configuration.py` file to change the directories there.

### Talon HUD environments

You can change your HUD layout entirely using the context management of Talon, saving you from having to say voice commands to set up your desired content and layout.  
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

## Miscellaneous

### Roadmap

These are ideas that I want to implement in no specific order and with no specific timeline in mind.

- Making the HUD screen reader friendly
- Bringing in tunable audio queues for stuff like mode switching, command registering et cetera
- An image panel with a header and a close icon which displays image content
- Splitting out or merging topics from widgets into separate widgets using voice
- Better default image, dimension and font scaling based on physical dimensions of the screen

If any of these ideas seem cool for you to work on, give me a message on the talon slack so we can coordinate stuff.

### Development philosophy and guidelines

The general idea of this repository is to separate out three concepts, the users UI preferences, the content on display and the actual display logic.  
These three silos are based on assumptions for three persona's. The User, the Scripter and the Themer.

The **User** wants to have their content displayed in a way that matches their intentions.  
They decide where they want to place their widgets, what dimensions the widgets should have, what theme should be on display and what size the font should be. After all, the User might be colour blind or have a reduced field of vision. This repository aims to accomodate to them.  
The User preferably doesn't have to change code when changing widgets around, and really doesn't want to lose their carefully crafted preferences or change their voice workflow around.

The **Scripter** wants to display their awesome creations in a visually appealing way without actually having to write out all the code required for that. They spent a bunch of time making an output that is useful, like an autocomplete feature or a command log, and they really don't want to spend more time fiddling around with canvas stuff.  
The Scripter just sends their content over to the HUD, which knows where the user wants it and in what way.

The **Themer** wants to make an amazing visual experience happen, but do not really want to deal with the nitty gritty details of the widgets themselves. They want to change icons, colours and other visual properties of the UI themselves. And they do not like being limited, preferably having as much freedom of expression as possible.  

These three persona's are the spirit of this repository. As such, when new content is added to this repository, it should try to adhere to the needs and wishes above.

#### Voice command guidelines

This repository tries to adhere to "What you see is what you say". If there is a widget with a header title, we make sure the widget can be addressed with that header name.  
Likewise, if there is a button on display on the screen, just reading the text on the button should activate it.  
If these options aren't available, documentation must be supplied with easily parseable voice commands so the users workflow is impacted minimally by reading large swats of text.

### Acknowledgements

The icons used are taken from https://icons.getbootstrap.com/.  
Some of the icons like the copy icon are taken from fontawesome.

The language icons are made by https://www.freepik.com hosted on https://www.flaticon.com/.  
If your language isn't in the themes, you can download icons for free with attribution of freepik.com and change their size to 35x35 before saving them as a .png file in your theme.

The programming language icons are taken from various icon packs, including Pictonic Icons, Material design, File by John Gardner and LibreICONS Black by DiemenDesign. Initial work for turning the programming languages into an icon was done by [@Wen Kokke](https://github.com/wenkokke).

The walkthrough system has been expanded with help and feedback from [@Tara roys](https://github.com/tararoys) and [@Pokey Rule](https://github.com/pokey) to be more user friendly to use and to create for.