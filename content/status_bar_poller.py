from talon import actions, cron, scope, speech_system, ui, app, Module
from user.talon_hud.content.poller import Poller
from user.talon_hud.content.state import hud_content

# Polls the current mode state to be displayed in widgets like the status bar
# Inspired by knausj forced languages
class StatusBarPoller(Poller):
    job = None
    current_lang_forced = False
    previous_mode = "command"
    
    def enable(self):
        if (self.job is None):
            self.job = cron.interval('100ms', self.state_check)

    def disable(self):
        cron.cancel(self.job)
        self.job = None

    def state_check(self):
        mode = self.determine_mode()
        if mode != self.previous_mode:
            hud_content.trigger_audio_cue('Mode change ' + mode)
            self.previous_mode = mode
    
        content = {
            'mode': self.determine_mode(),
            'language': self.determine_language(),
            'programming_language': {
                'ext': self.get_lang_extension(self.determine_programming_language()),
                'forced': self.current_lang_forced and self.determine_mode() != "dictation"
            }
        }
                
        hud_content.update(content)        
                
    # Determine three main modes - Sleep, command and dictation
    def determine_mode(self):
        active_modes = scope.get('mode')

        # If no mode is given, just show command
        mode = 'command' 
        if ( active_modes is not None ):
            if ('sleep' in active_modes):
                mode = 'sleep'
            if ('dictation' in active_modes):
                mode = 'dictation'
        
        return mode
        
    # Language map added from knausj
    language_to_ext = {
        "assembly": ".asm",
        "batch": ".bat",
        "c": ".c",
        "cplusplus": ".cpp",
        "csharp": ".c#",
        "gdb": ".gdb",
        "go": ".go",
        "lua": ".lua",
        "markdown": ".md",
        "perl": ".pl",
        "powershell": ".psl",
        "python": ".py",
        "ruby": ".rb",
        "bash": ".sh",
        "snippets": "snip",
        "talon": ".talon",
        "vba": ".vba",
        "vim": ".vim",
        "javascript": ".js",
        "typescript": ".ts",
        "r": ".r",
    }
    
    # Determine the forced or assumed language
    def determine_programming_language(self): 
        lang = actions.code.language()
        if (not lang):  
            active_modes = scope.get('mode')
            if (active_modes is not None):
                for index, active_mode in enumerate(active_modes):
                    if (active_mode.replace("user.", "") in self.language_to_ext):
                        self.current_lang_forced = True
                        return active_mode.replace("user.", "")
            return ""
        else:
            self.current_lang_forced = False
            return lang if lang else ""
        
    def determine_language(self):
        return scope.get('language')
        
    def get_lang_extension(self, language):
        if (language in self.language_to_ext):
            return self.language_to_ext[language]
        else:
            ''
            
def on_ready():
    actions.user.hud_register_audio_cue('Mode change sleep', "Triggers whenever talon enters sleep mode", "sleep_mode")
    actions.user.hud_register_audio_cue('Mode change command', "Triggers whenever talon enters command mode", "command_mode")
    actions.user.hud_register_audio_cue('Mode change dictation', "Triggers whenever talon enters dictation mode", "pen")        
    
app.register('ready', on_ready)