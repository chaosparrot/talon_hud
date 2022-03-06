
The HUD is a user interface that helps improve your workflow. Inspired by gaming HUDs, it is meant to show just the right amount of info to your screen without getting in the way of your actual work.  
It is resizable, scalable and placable in whatever combination you can come up with, so only the screen space that you allow will be used, just as you left it.  
It combines voice commands with clickable buttons, allowing for seemless transitions between using your regular old controls and your voice command flow.  

On top of that, the HUD remembers where you left off. It keeps the widgets in the place you have left them for the next time you start up, and when you add or remove monitors, it will remember where you kept the widgets in those instances.  
This makes the HUD excellent for switching between a single laptop screen, and connecting a monitor in the office or at home.

By default, the HUD comes in a light and a dark mode, but you can create other themes yourself as well!

## Available content

### Microphone muting / management

In some scenario's like conference calls, it is handy to have a way to instantly turn off the microphones input to Talon. This toggle can be placed on the status bar by saying `status bar add microphone` or right clicking on the status bar and selecting 'Add microphone'.  
Switching the microphone off this way prevents accidental wake messages or commands from triggering functionality while you are talking to your friends or colleges.

On top of that, you can also switch microphones on the fly by saying `toolkit microphones`, or right clicking the status bar and following Content toolkit -> Microphones. The microphone selected here will be used as a favorite setting, so if you toggle the microphone on and off, it will remember the selected microphone here and switch back to that microphone.  
This comes in handy when you have multiple microphone set ups, like a laptop microphone and an on desk microphone.

### Talon Mode tracking ( turned on by default )

Talon comes in a variety of modes, like the command mode in which you utter commands, or the sleep mode where no commands are used but the wake word. To keep track of what mode you are currently in, the Talon HUD offers a status bar icon that can be clicked. 
This is added by default, and when clicked, turns Talon either in sleep mode, or from sleep mode back to your previous mode, be it command or dictation mode.  
Removing the mode icon is possible as well to keep a more minimal look, by saying `status bar remove mode indicator` or by right clicking the status bar and clicking 'Remove mode indicator'.  
The status bar will always show whether you are in sleep mode or not at a glance, regardless of when you have mode icon added or not, by changing the appearance of the status bar itself.  

You can change the mode detection, toggle and available modes yourself as well, if your set up requires a more personal touch. To see how, read the link below.

(TODO!)[Customizing mode tracking]

### Speech history ( turned on by default )

Taking inspiration from FPS games, the event log widget allows you to read back voice commands as you make them, as well as clearing themselves up after a few seconds to give you back that screen space.  
Different options to show commands are available. You can keep the commands visible indefinitely, or temporarily freeze them to discuss them, perfect for pairing sessions.  

If you need are more in-depth view of the commands said, you can say `toolkit speech` or navigate from the status bar with Content toolkit -> Debugging -> Speech to find a full overview of the commands said, as well as the used engine and microphone.

### Language tracking

For the multi-lingual folks out there, switching between different languages for dictation is a necessity to keep your workflow working with voice. For that purpose, you can add a language icon indicating your language on the status bar by saying `status bar add language` or right clicking the status bar to the option Add language.  

(TODO!)[Customizing programming languages]

### Programming language tracking

A lot of programmers inhabit the Talon Voice community, and with them come many different programming languages. With those programming languages come different commands, and usually these are kept track of by the file extension available in a program, or by manually forcing a certain language to be used.  
To make sure you know what programming language context you are in, you can add a language icon to your status bar by saying `status bar add code language` or right clicking the status bar and clicking 'Add code language'.  
You can add and remove programming languages icons yourself, by following the instructions below.  

(TODO!)[Customizing programming languages]

### Focus tracking

When returning back to your computer after a while, it can be hard to see what window Talon has focused for voice commands. This only gets harder if you have multiple monitors. To alleviate this problem, you can add a focus indicator to your status bar by saying `status bar add focus indicator` or right clicking the status bar and selecting 'Add focus indicator'.  
This will present an orange-red box on the top center of the currently focused window, to remind you what direction you're talking to.