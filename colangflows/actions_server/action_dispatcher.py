"""Module for the calling proper action endpoints based on events received at action server endpoint """

import logging
from typing import Any, Dict, List, Tuple, Union

from colangflows.actions.langchain_tools.wiki import Wikipedia
from colangflows.actions.langchain_tools.wolfram_alpha import WolframAlpha

# Langchain actions import

log = logging.getLogger(__name__)


class ActionDispatcher:
    _registered_actions = {"wikipedia": Wikipedia, "WolframAlpha": WolframAlpha}

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
