"""Module for the calling proper action endpoints based on events received at action server endpoint """

import importlib.util
import inspect
import logging
import os
from typing import Any, Dict, List, Tuple, Union

log = logging.getLogger(__name__)


class ActionDispatcher:
    _registered_actions = {}

    def __init__(self):
        log.info("Starting action dispatcher")

        # TODO: check for better way to find actions dir path or use constants.py
        action_path = os.path.join(os.path.dirname(__file__), "..", "actions")
        self._registered_actions = self._find_action_classes(action_path)
        log.info(f"Registered Actions: {self._registered_actions}")
        log.info("Action dispatcher initialized")

    def execute_action(
        self, action_name: str, params: Dict[str, Any]
    ) -> Tuple[Union[str, Dict[str, Any]], str]:
        """Endpoint called from action server to execute an action.
        This endpoint interacts with different supported actions
        """

        if action_name in self._registered_actions:
            log.info(f"Executing registered action: {action_name}")
            fn = self._registered_actions.get(action_name, None)
            if fn is not None:
                try:
                    obj = fn(**params)
                    result = obj.run()
                    if isinstance(result, str):
                        return {"text": result}, "success"
                    else:
                        return result, "success"
                except Exception as e:
                    log.info(f"Error {e} while execution {action_name}")

        return {}, "failed"

    def get_registered_actions(self) -> List[str]:
        """Endpoint called from action server to get the list of available actions"""
        return list(self._registered_actions.keys())

    def _find_action_classes(self, directory) -> Dict:
        """Loop through all the subdirectories and check for the class with @action
        decorator and add in action_classes dict
        """
        action_classes = {}

        # Loop through all files in the directory and its subdirectories
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith(".py"):
                    try:
                        # Import the module from the file
                        filepath = os.path.join(root, filename)
                        spec = importlib.util.spec_from_file_location(
                            filename, filepath
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Loop through all members in the module and check for the `@action` decorator
                        # If class has action decoratore is_action class member is true
                        for name, obj in inspect.getmembers(module):
                            # check given object is class and belongs to same file(not imported)
                            if (
                                inspect.isclass(obj)
                                and hasattr(obj, "__dict__")
                                and hasattr(obj.__dict__, "get")
                                and obj.__dict__.get("__module__")
                                and obj.__dict__.get("__module__") == module.__name__
                            ):
                                # check if is_action is true in object
                                if hasattr(obj, "is_action") and obj.is_action == True:
                                    log.info(f"Adding {obj.__name__} to actions")
                                    action_classes[obj.__name__] = obj
                    except Exception as e:
                        log.debug(
                            f"Failed to register {filename} in action dispatcher due to exception {e}"
                        )

        return action_classes
