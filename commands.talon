^head up (show|open)$: user.enable_hud()
^head up theme dark$: user.switch_hud_theme("dark")
^head up theme light$: user.switch_hud_theme("light")
^head up drag$: user.set_hud_setup_mode("position")
^head up (drop|stop)$: user.set_hud_setup_mode("")
^head up (hide|close)$: user.disable_hud()

action(user.activate_statusbar_icon_mode): speech.disable()
action(user.activate_statusbar_icon_close): user.disable_hud()