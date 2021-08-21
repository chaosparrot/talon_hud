from talon import skia, ui, Module, cron, actions, clip
from user.talon_hud.widgets.textpanel import HeadUpTextPanel
from user.talon_hud.widget_preferences import HeadUpDisplayUserWidgetPreferences

class HeadUpDocumentationPanel(HeadUpTextPanel):
    preferences = HeadUpDisplayUserWidgetPreferences(type="documentation_panel", x=50, y=50, width=400, height=300, limit_x=50, limit_y=50, limit_width=500, limit_height=700, enabled=False, alignment="left", expand_direction="down", font_size=18)
