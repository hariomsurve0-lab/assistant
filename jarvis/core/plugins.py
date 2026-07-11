import os
import importlib
import inspect
from jarvis.logger import logger

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")

class PluginManager:
    def __init__(self):
        self.commands = {}
        self.load_plugins()

    def load_plugins(self):
        self.commands.clear()
        if not os.path.exists(SKILLS_DIR):
            logger.warning(f"[Plugins] Skills directory not found: {SKILLS_DIR}")
            return
            
        for file in os.listdir(SKILLS_DIR):
            if file.endswith(".py") and not file.startswith("__"):
                module_name = f"jarvis.skills.{file[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    # Reload module in case it changed
                    importlib.reload(module)
                    
                    # Look for functions in the module
                    for name, func in inspect.getmembers(module, inspect.isfunction):
                        # Register all functions that don't start with underscore
                        if not name.startswith("_"):
                            self.commands[name] = func
                            logger.info(f"[Plugins] Registered command skill: {name} from {module_name}")
                except Exception as e:
                    logger.error(f"[Plugins] Failed to load module {module_name}: {e}")
        logger.info(f"[Plugins] Completed loading {len(self.commands)} command skills.")

_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
