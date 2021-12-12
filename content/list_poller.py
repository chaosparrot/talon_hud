from talon import actions, cron, registry, ui, app, Module
from user.talon_hud.content.poller import Poller

# Polls the current Talon registry lists for debugging purposes
class ListPoller(Poller):
    job = None
    previous_list_state = ''
    list = None

    def enable(self):
       if (self.job is None):
            self.enabled = True
            scope_state = self.get_list_in_text()        
            actions.user.hud_publish_content(scope_state, 'list', 'List inspection')        
            
            self.job = cron.interval('200ms', self.list_check)
                
    def disable(self):
        cron.cancel(self.job)
        self.job = None
        self.enabled = False

    def list_check(self):        
        list_state = self.get_list_in_text()
        if (list_state != self.previous_list_state):
            self.previous_list_state = list_state
            actions.user.hud_publish_content(list_state, 'list', 'List inspection', False)
        
    def get_list_in_text(self):
        content = ""
        if self.list in registry.lists:
            list_contents = registry.lists[self.list][0]
            
            list_description = registry.decls.lists[self.list].desc if self.list in registry.decls.lists else ""
            if len(list_contents) == 0:
                content = "<*" + self.list + "/>\n" + list_description + "\n\n"
            else:
                content = "<*" + self.list + "(" + str(len(list_contents)) + ")/>\n" + list_description + "\n\n"                
            
                # Bundle same values together so we have all the synonyms bundled
                content_choices = {}
                for option in list_contents:
                    if list_contents[option] not in content_choices:
                        content_choices[ list_contents[option] ] = []
                        
                    content_choices[list_contents[option]].append( option )\
                
                for value in content_choices:
                    content += "<*" + "/><!! or /><*".join(content_choices[value]) + "/>: " + value + "\n"
        elif self.list is not None:
            content = "<*" + self.list + "/>\nList no longer exists!"
        
        return content
        
def select_list(data):
    list_poller = ListPoller()
    list_poller.list = data["text"]
    actions.user.hud_add_poller('list', list_poller)
    actions.user.hud_activate_poller('list')

mod = Module()
@mod.action_class
class Actions:

    def hud_toolkit_lists():
        """Show available filled lists to view for the Talon HUD"""
        lists = registry.lists
        choices = []
        for index, key in enumerate(lists):
            if lists[key] and lists[key][0]:
                choices.append({"text": key})
        
        choices = actions.user.hud_create_choices(choices, select_list)
        actions.user.hud_publish_choices(choices, "Toolkit lists", "Select a list to inspect by saying <*option <number>/> or saying the name of the list")
        
