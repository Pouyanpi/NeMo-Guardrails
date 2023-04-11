import logging
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from colangflows.actions.actions import ActionResult
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
        default={}, description="The list of action parameters."
    )


class ResponseBody(BaseModel):
    status: str = "success"  # success / failed
    results: dict = Field(
        default={}, description="The new messages in the conversation"
    )


@app.post(
    "/v1/action/run",
    summary="execute actions with give param.",
    response_model=ResponseBody,
)
def run_action(body: RequestBody):
    """Execute action_name with action_parameters and return result."""

    log.info(f"Request body: {body}")
    result, status = app.action_dispatcher.execute_action(
        body.action_name, body.action_parameters
    )
    resp = {"status": status, "results": result}
    log.info(f"Response: {resp}")
    return resp


@app.get(
    "/v1/action/list",
    summary="Get List of available actions.",
)
def get_actions_list():
    """Returns the list of available actions."""

    return app.action_dispatcher.get_registered_actions()
