tag: user.talon_hud_available
-
# General HUD commands
^head up (show|open)$: user.hud_enable()
^head up theme {user.talon_hud_themes}$: user.hud_switch_theme(talon_hud_themes)
^head up (drop|stop|confirm)$: user.hud_set_setup_mode("*", "")
^head up cancel$: user.hud_set_setup_mode("*", "cancel")
^head up (hide|close)$: user.hud_disable()

# Widget setup commands
^head up (show|open) {user.talon_hud_widget_names}$: user.hud_enable_id(talon_hud_widget_names)
^head up (hide|close) {user.talon_hud_widget_names}$: user.hud_disable_id(talon_hud_widget_names)
^head up resize {user.talon_hud_widget_names}$: user.hud_set_setup_mode(talon_hud_widget_names, "dimension")
^head up expand {user.talon_hud_widget_names}$: user.hud_set_setup_mode(talon_hud_widget_names, "limit")
^head up text scale {user.talon_hud_widget_names}$: user.hud_set_setup_mode(talon_hud_widget_names, "font_size")
^head up drag {user.talon_hud_widget_names}+$: 
    user.hud_set_setup_mode_multi(talon_hud_widget_names_list, "position")
^head up basic {user.talon_hud_widget_names}$: user.hud_set_widget_preference(talon_hud_widget_names, "show_animations", 0)
^head up fancy {user.talon_hud_widget_names}$: user.hud_set_widget_preference(talon_hud_widget_names, "show_animations", 1)
^head up hide {user.talon_hud_widget_names} on sleep$: user.hud_set_widget_preference(talon_hud_widget_names, "sleep_enabled", 0)
^head up show {user.talon_hud_widget_names} on sleep$: user.hud_set_widget_preference(talon_hud_widget_names, "sleep_enabled", 1)
^head up align {user.talon_hud_widget_names} right$: user.hud_set_widget_preference(talon_hud_widget_names, "alignment", "right")
^head up align {user.talon_hud_widget_names} left$: user.hud_set_widget_preference(talon_hud_widget_names, "alignment", "left")
^head up align {user.talon_hud_widget_names} center$: user.hud_set_widget_preference(talon_hud_widget_names, "alignment", "center")
^head up align {user.talon_hud_widget_names} top$: user.hud_set_widget_preference(talon_hud_widget_names, "expand_direction", "down")
^head up align {user.talon_hud_widget_names} bottom$: user.hud_set_widget_preference(talon_hud_widget_names, "expand_direction", "up")

# Widget content commands
^{user.talon_hud_widget_names} (show|open)$: user.hud_enable_id(talon_hud_widget_names)
^{user.talon_hud_widget_names} (hide|close)$: user.hud_disable_id(talon_hud_widget_names)
^{user.talon_hud_widget_names} minimize$: user.hud_set_widget_preference(talon_hud_widget_names, "minimized", 1)
^{user.talon_hud_widget_names} maximize$: user.hud_set_widget_preference(talon_hud_widget_names, "minimized", 0)
^{user.talon_hud_widget_names} next: user.hud_increase_widget_page(talon_hud_widget_names)
^{user.talon_hud_widget_names} (back|previous): user.hud_decrease_widget_page(talon_hud_widget_names)
^{user.talon_hud_widget_names} options: user.hud_widget_options(talon_hud_widget_names)

# Head up audio commands
^head up audio enable$: user.hud_audio_enable()
^head up audio (disable|mute)$: user.hud_audio_disable()
^head up audio volume {user.talon_hud_volume_number} [percent]$: user.hud_audio_set_volume(talon_hud_volume_number)
^head up audio enable {user.talon_hud_audio}$: user.hud_audio_enable(talon_hud_audio)
^head up audio (disable|mute) {user.talon_hud_audio}$: user.hud_audio_disable(talon_hud_audio)
^head up audio {user.talon_hud_audio} volume {user.talon_hud_volume_number} [percent]$: user.hud_audio_set_volume(talon_hud_volume_number, talon_hud_audio)

# Head up focus commands
^(head up focus | focus head up):
    user.hud_focus()
^head up blur:
    user.hud_blur()
^head up [enable] auto focus:
    user.hud_set_auto_focus(1)
^head up disable auto focus:
    user.hud_set_auto_focus(0)

# Head up development commands - Sets watchers on certain configurations, like themes, so development is quicker
^head up development start$: 
    user.hud_watch_directories()
    user.hud_watch_walkthrough_files()
    user.hud_watch_documentation_files()
^head up development stop$: 
    user.hud_unwatch_directories()
    user.hud_unwatch_walkthrough_files()
    user.hud_unwatch_documentation_files()
