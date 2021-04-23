^head up (show|open)$: user.enable_hud()
^head up theme dark$: user.switch_hud_theme("dark")
^head up theme light$: user.switch_hud_theme("light")
^head up (drop|stop|confirm)$: user.set_hud_setup_mode("*", "")
^head up cancel$: user.set_hud_setup_mode("*", "cancel")
^head up (hide|close)$: user.disable_hud()

^head up (show|open) status bar$: user.enable_hud_id("status_bar")
^head up (hide|close) status bar$: user.disable_hud_id("status_bar")
^head up resize status bar$: user.set_hud_setup_mode("status_bar", "dimension")
^head up drag status bar$: user.set_hud_setup_mode("status_bar", "position")

# Changable statusbar icon actions
action(user.activate_statusbar_icon_mode): speech.disable()
action(user.activate_statusbar_icon_close): user.disable_hud()

^head up (show|open) event log$: user.enable_hud_id("event_log")
^head up (hide|close) event log$: user.disable_hud_id("event_log")
^head up resize event log$: user.set_hud_setup_mode("event_log", "dimension")
^head up drag event log$: user.set_hud_setup_mode("event_log", "position")
^head up align event log right$: user.set_widget_preference("event_log", "alignment", "right")
^head up align event log left$: user.set_widget_preference("event_log", "alignment", "left")
^head up expand event log up$: user.set_widget_preference("event_log", "expand_direction", "up")
^head up expand event log down$: user.set_widget_preference("event_log", "expand_direction", "down")