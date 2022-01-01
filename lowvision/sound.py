from talon import scope, cron, app
import winsound
import os
import time

mode = "sleep"

def check_mode_changed():
    global mode
    print( mode )
    if "command" in scope.get("mode"):
        if mode not in scope.get("mode"):
            mode = "command"    
            path = os.path.dirname(os.path.realpath(__file__))
            flags = winsound.SND_FILENAME + winsound.SND_NODEFAULT + winsound.SND_ASYNC
            winsound.PlaySound(os.path.join(path, "command_mode.wav"), flags)
    else:
        mode = "sleep"
    
def ready_thing():
    cron.interval("500ms", check_mode_changed)

app.register("ready", ready_thing)


