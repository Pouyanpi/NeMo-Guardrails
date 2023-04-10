import logging
import os.path
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from colangflows.rails import LLMRails, RailsConfig

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

api_description = """Colang Flows Sever API."""


app = FastAPI(
    title="Colang Flows Server API",
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


class RequestBody(BaseModel):
    config_id: str = Field(description="The id of the configuration to be used.")
    messages: List[dict] = Field(
        default=None, description="The list of messages in the current conversation."
    )


class ResponseBody(BaseModel):
    messages: List[dict] = Field(
        default=None, description="The new messages in the conversation"
    )


@app.get(
    "/v1/rails/configs",
    summary="Get List of available rails configurations.",
)
def get_rails_configs():
    """Returns the list of available rails configurations."""

    # Currently, we return the list of rails config from the examples folder
    rails_config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "examples", "rails"
    )

    # We extract all folder names as config names
    config_ids = [
        f
        for f in os.listdir(rails_config_path)
        if os.path.isdir(os.path.join(rails_config_path, f))
    ]

    # If there is a "config" folder in the current folder, we also use that
    local_path = os.getcwd()
    local_configs_path = os.path.join(local_path, "config")

    local_config_ids = []
    if os.path.exists(local_configs_path):
        local_config_ids = [
            f
            for f in os.listdir(local_configs_path)
            if os.path.isdir(os.path.join(local_configs_path, f))
        ]

    return [{"id": config_id} for config_id in (config_ids + local_config_ids)]


# One instance of LLMRails per config id
llm_rails_instances = {}

# The history per config id
# TODO: this is quick hack, not meant to be released like this.
#   We should either have caching on conversation history or explicit state passing mechanism.
history = {}


def _get_rails(config_id: str) -> LLMRails:
    """Returns the rails instance for the given config id."""
    if config_id in llm_rails_instances:
        return llm_rails_instances[config_id]

    rails_config_path = os.path.join("examples/rails", config_id)
    local_config_path = os.path.join(os.getcwd(), "config", config_id)

    if os.path.exists(rails_config_path):
        rails_config = RailsConfig.from_path(rails_config_path)
    elif os.path.exists(local_config_path):
        rails_config = RailsConfig.from_path(local_config_path)
    else:
        raise ValueError(f"Could not find rails configuration {config_id}")

    llm_rails = LLMRails(config=rails_config)
    llm_rails_instances[config_id] = llm_rails
    history[config_id] = []

    return llm_rails


@app.post(
    "/v1/chat/completions",
    response_model=ResponseBody,
)
async def chat_completion(body: RequestBody):
    """Chat completion for the provided conversation.

    TODO: add support for explicit state object.
    """
    log.info("Got request for config %s", body.config_id)

    config_id = body.config_id
    llm_rails = _get_rails(config_id)
    history[config_id].append(body.messages[-1])

    bot_message = await llm_rails.generate_async(messages=history[config_id])
    history[config_id].append(bot_message)

    return {"messages": [bot_message]}


# Finally, we register the static frontend UI serving

FRONTEND_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "chat-ui", "frontend"
)

app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True,
    ),
    name="chat",
)
