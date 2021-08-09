from talon import actions, cron, scope, speech_system, ui
from user.talon_hud.content.state import hud_content

# Polls the current state using knausj bindings
# Used several bindings from the knausj repository like history
# TODO - Make this dynamic based on events
class KnausjStatePoller:
    
    job = None
    enabled = False
    current_lang_forced = False
    
    previous_scope_state = ''
    
    def enable(self):
        if (self.enabled != True):
            self.enabled = True
            speech_system.register("phrase", self.on_phrase)
            if (self.job is None):
                self.job = cron.interval('100ms', self.state_check)
                

    def disable(self):
        if (self.enabled != False):
            self.enabled = False        
            speech_system.unregister("phrase", self.on_phrase)
            if (self.job is not None):
                cron.cancel(self.job)
            self.job = None

    def state_check(self):
        content = {
            'mode': self.determine_mode(),
            'language': self.determine_language(),
            'programming_language': {
                'ext': self.get_lang_extension(self.determine_programming_language()),
                'forced': self.current_lang_forced and self.determine_mode() != "dictation"
            },
        }
        
        hud_content.update(content)
        
        scope_state = self.get_state_in_text()
        if (scope_state != self.previous_scope_state):
            self.previous_scope_state = scope_state
            actions.user.hud_publish_content(scope_state, 'scope', 'Scope panel', False, [])
            
    def on_phrase(self, j):
        try:
            word_list = getattr(j["parsed"], "_unmapped", j["phrase"])
        except:
            word_list = j["phrase"]
        hud_content.append_to_log("command", " ".join(word.split("\\")[0] for word in word_list))
    
    # Determine three main modes - Sleep, command and dictation
    def determine_mode(self):
        active_modes = scope.get('mode')

        # If no mode is given, just show command
        mode = 'command'
        if ( active_modes is not None ):
            if ('sleep' in active_modes):
                mode = 'sleep'
            if ('user.parrot_switch' in active_modes):
                mode = 'parrot_switch'
            if ('dictation' in active_modes):
                mode = 'dictation'
        
        return mode
        
    def get_state_in_text(self):
        tags = scope.get('tag')
        
        new_tags = []
        if tags is not None:
            for tag in tags:
                new_tags.append(tag)
                
        modes = []
        scopemodes = scope.get('mode')
        if scopemodes is not None:
            for mode in scopemodes:
                modes.append(mode)
                
        text = "<*App: " + scope.get('app')['name'] + "/>\n" + scope.get('win')['title'] + "/>\n<*<+Tags:/>/>\n" + "\n".join(sorted(new_tags)) + "\n<*<!Modes:/>/>  " + " - ".join(sorted(modes))
        return text
    
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