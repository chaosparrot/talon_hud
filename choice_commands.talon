tag: user.talon_hud_available
and tag: user.talon_hud_visible
and tag: user.talon_hud_choices_visible
-
[option] {user.talon_hud_choices}: user.hud_activate_choice(talon_hud_choices)
option {user.talon_hud_numerical_choices}+$: user.hud_activate_choices(talon_hud_numerical_choices_list)

# This allows for the text 'option one five four confirm' to make quick confirmation possible
option {user.talon_hud_numerical_choices}+ {user.talon_hud_choices}$:
    user.hud_activate_choices(talon_hud_numerical_choices_list)
	user.hud_activate_choice(talon_hud_choices)

# This allows for dynamic voice commands to be added without changing the context available in the headers of talon files
{user.talon_hud_widget_enabled_voice_commands}: user.hud_activate_enabled_voice_command(talon_hud_widget_enabled_voice_commands)