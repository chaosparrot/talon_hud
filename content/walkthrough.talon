tag: user.talon_hud_available
and tag: user.talon_hud_visible
and tag: user.talon_hud_walkthrough
-
read more: user.increase_widget_page("walk_through")
skip step: 
    sleep(1.5)
    user.hud_skip_walkthrough_step()
skip everything: user.hud_skip_walkthrough_all()
previous step: 
    user.hud_previous_walkthrough_step()
^head up theme dark$:
    sleep(0.5)
	user.switch_hud_theme('dark')
^head up theme light$: 
    sleep(1.5)
	user.switch_hud_theme('light')
^music and video playlist$:
    user.open_url("https://www.youtube.com/watch?v=lyVICt4vdB0&list=PLEelxuGt2Io5jGNnA44S9lRhclhz7po1U&index=1")