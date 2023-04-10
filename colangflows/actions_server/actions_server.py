import logging
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from colangflows.actions_server.action_dispatcher import ActionDispatcher

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

api_description = """Colang Flows Action Sever API."""


app = FastAPI(
    title="Colang Flows Action Server API",
    description=api_description,
    version="0.1.0",
    terms_of_service="https://www.nvidia.com/en-us/about-nvidia/privacy-policy/",
    license_info={"name": "NVIDIA Proprietary"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create action dispatcher object to communicate with actions
app.action_dispatcher = ActionDispatcher()


class RequestBody(BaseModel):
    action_name: str = ""
    action_parameters: Dict = Field(
        default=None, description="The list of action parameters."
    )


@app.post(
    "/v1/action/run",
    summary="execute actions with give param.",
)
def run_action(body: RequestBody):
    """Execute action_name with action_parameters and return result."""

    # TODO: Maintain an object of action dispatcher and pass action parameters
    log.info(f"Request body: {body}")
    return {"action-name": body.action_name, "param": body.action_parameters}


# TODO: Implement get action to get list of available actions
@app.get(
    "/v1/action/list",
    summary="Get List of available actions.",
)
def get_actions_list():
    """Returns the list of available actions."""

    return []
