import importlib
import logging

logger = logging.getLogger(__name__)

class LazyLoader:
    def __init__(self):
        self._loaded_modules = {}

    def get_module(self, module_path: str, class_name: str = None):
        try:
            if module_path in self._loaded_modules:
                module = self._loaded_modules[module_path]
            else:
                logger.info(f"Lazy loading module: {module_path}")
                module = importlib.import_module(module_path)
                self._loaded_modules[module_path] = module
            if class_name:
                return getattr(module, class_name)
            return module
        except ImportError as e:
            logger.error(f"Failed to import {module_path}: {e}")
            return None
        except AttributeError as e:
            logger.error(f"Class {class_name} not found in {module_path}: {e}")
            return None

loader = LazyLoader()
