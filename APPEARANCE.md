# Appearance and theming

The HUD's appearance is almost fully changeable without having to dive into nitty gritty code. Depending on the widget, a number of values can be tweaked like colours, border thickness and paddings, and so on. The images are also neatly kept inside of a folder for you to change as you wish. 
All of these things are bundled in a 'theme'. The light theme is the one you see when you start up. You can find the themes inside of the themes folder.

By default, there are two available themes - Light and dark, for a light and dark mode. These you can switch using `head up theme dark` and `head up theme light`.

## Customizing appearance

In order to change a theme, you only really need two things.
- A program that can open a CSV file like Excel
- A way to generate HEX color codes ( There is plenty of online tools for that, like the [duckduckgo colorpicker](https://duckduckgo.com/?q=color+picker&t=h_&ia=answer) where you can simply pick your color and copy the text next to the # )

Before tweaking themes, it is recommended to turn the HUD in development mode by saying `head up development start`, that way when you save the file, it will automatically update the widgets accordingly. When you are done tweaking the values, saying `head up development stop` will turn the HUD back into its regular non-autoreloading mode.

Inside the themes.csv file inside themes/light you will find a list of values that you can change, for instance the command_mode_colour which is currently set to #FFFFFF. If you change this to a different value, like #0000AA which is the color blue, it will display a blue colour on your status bar. If there is a problem with a colour not showing up properly, check your Talon log for any Talon HUD warnings that show up.  

You will notice that inside of the light theme folder, there are no images to be found. That is because all the themes take the images out from a single base theme inside of _base_theme. You can change the images around here and they will be used for all the available themes. As long as you use the right file names, the images should update nicely.

If you wish to change the images around for the light theme only, you can copy the images folder inside of the _base_theme folder over to the light folder, and change the images around. The images are only reloaded whenever you change a theme, or whenever you change a file when the HUD is in the development mode.

## Creating your own theme

You can create your own theme by simply copying an existing theme over. If you place the copied theme inside of the themes folder and change its name while in development mode, it will be automatically registered. Lets say you have created the folder 'blue', you can then change to that theme by saying `head up theme blue`. You can tweak it as you wish up like described in the Customizing appearance part above.

You do not necessarily need to place your theme inside of the themes folder, you can also place it somewhere else and register it manually using the action `user.hud_register_theme`. An example is shown below.

```python
from talon import app, actions

def register_custom_theme():
    actions.user.hud_register_theme("blue", "PATH_TO_BLUE_THEME_HERE")

app.register("ready", register_custom_theme)
```

## Tweakable values for themes.csv:

TODO - Explain every value inside themes.csv