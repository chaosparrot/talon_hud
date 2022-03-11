from talon import Module, actions, cron
from typing import Any
import copy

key_hud = "HeadUpDisplay"
key_content = "HeadUpDisplayContent"
key_poller = "Poller"

_reloader_state = {
    "HeadUpDisplay": [],
    "HeadUpDisplayContent": [],
    "Poller": {}
}

def clear_old_references():
    global _reloader_state
    
    #print( "CLEARING!" )
    for index, hud in enumerate(_reloader_state[key_hud]):
    #    print( "RELOAD HUD INDEX", index, len(_reloader_state[key_hud]) - 1 )
        if index != len(_reloader_state[key_hud]) - 1:
    #        print( "CLEARING", index )
            _reloader_state[key_hud][index] = None
    _reloader_state[key_hud] = [_reloader_state[key_hud][-1]]
    
    # Keep the first content state around as it is the most likely to be filled
    content_topic_types = copy.copy(_reloader_state[key_content][0].topic_types) if len(_reloader_state[key_content]) > 0 else {}    
    for key in _reloader_state:
        if key not in [key_hud, key_poller]:
    #        print( "RELOAD " + key, index, len(_reloader_state[key]) - 1 )
            for index, extra_type in enumerate(_reloader_state[key]):
                if index != len(_reloader_state[key]) - 1:
    #                print( "CLEARING", index )
                    _reloader_state[key][index] = None
            _reloader_state[key] = [_reloader_state[key][-1]]
    
    if len(_reloader_state[key_content]) > 0:
        _reloader_state[key_content][0].topic_types = content_topic_types
    _reloader_state[key_hud][-1].start()

clean_older_references_job = None

mod = Module()
@mod.action_class
class Actions:

    def hud_internal_register(type: str, data: Any, name: str = None):        
        """Used to register new instances of HeadUpDisplay, HeadUpDisplayContent etc. for managing between reloads caused by file updates"""
        global _reloader_state
        global clean_older_references_job
        
        keep_alive_pollers = []
        if len(_reloader_state[key_hud]) > 0:
            keep_alive_pollers = _reloader_state[key_hud][0].keep_alive_pollers[:]
        
        if type == key_hud:
            if len(_reloader_state[key_hud]) > 0:
                for hud in _reloader_state[key_hud]:
                    if hud:
                        hud.destroy()
            
            # Connect the latest HUD object to the latest content and other objects
            _reloader_state[key_hud].append(data)
            for key in _reloader_state:
                if key == key_poller:
                    for name in _reloader_state[key_poller]:
                        data.register_poller(name, _reloader_state[key_poller][name], name in keep_alive_pollers)
                elif len(_reloader_state[key]) > 0:
                    data.connect_internal(key, _reloader_state[key][-1])
            
            cron.cancel(clean_older_references_job)
            clean_older_references_job = cron.after("50ms", clear_old_references)
        
        # Connect pollers to the HUD
        elif type == key_poller and name is not None:
            if name in _reloader_state[key_poller] and (hasattr(_reloader_state[key_poller][name], "enabled") and _reloader_state[key_poller][name].enabled):
                _reloader_state[key_poller][name].disable()
            _reloader_state[key_poller][name] = data
            
            if len(_reloader_state[key_hud] ) > 0:
                _reloader_state[key_hud][-1].register_poller(name, data, name in keep_alive_pollers)
                
        # All auxiliary types that connect to the HUD
        else:
            if type not in _reloader_state:
                _reloader_state[type] = []
                
            if len(_reloader_state[key_content]) > 0:
                for extra_type in _reloader_state[type]:
                    if extra_type and hasattr(extra_type, "destroy"):
                        extra_type.destroy()
                    else:
                        print( "Talon HUD - " + extra_type + " does not have a destroy method to clean up references during reloads" )
            _reloader_state[type].append(data)
            if len(_reloader_state[key_hud]) > 0:
                _reloader_state[key_hud][-1].connect_internal(type, data)
            
            cron.cancel(clean_older_references_job)
            clean_older_references_job = cron.after("50ms", clear_old_references)

