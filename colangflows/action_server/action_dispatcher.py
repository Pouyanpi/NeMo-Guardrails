"""Module for the calling proper action endpoints based on events received at action server endpoint """

from typing import Dict, List, Optional, Any
from colangflows.action_server.bash import Bash
from colangflows.action_server.actions import ActionResult

class ActionDispatcher():

    _registered_actions = {
        "langchain bash": Bash
    }

    def execute_action(self, params: Dict[str, Any]):
        """ Endpoint called from action server to execute an action.
            This endpoint actually interacts with different supported actions
        """

        action_name = params.get("action_name")

        if action_name in self._registered_actions:
            print(f"Executing registered action: {action_name}")
            fn = self._registered_actions.get(action_name)
            if fn == Bash:
                obj = fn(command=["ls"])
                result = obj.run()
                return ActionResult(return_value=result, events=[])


    def get_registered_actions(self):
        """ Endpoint called from action server to get the list of available actions
        """
        return list(self._registered_actions.keys())


if __name__ == "__main__":
    ad = ActionDispatcher()
    print(f"Available actions are: {ad.get_registered_actions()}")
    print(ad.execute_action({"action_name": "langchain bash"}))

