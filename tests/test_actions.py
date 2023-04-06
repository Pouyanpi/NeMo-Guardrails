import pytest
from fastapi.testclient import TestClient

from colangflows.actions_server import actions_server

client = TestClient(actions_server.app)


def test_run():
    response = client.post(
        "/v1/action/run",
        json={
            "action_name": "action-test",
            "action_parameters": {
                "content": "Hello",
                "parameter": "parameters",
            },
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["action-name"] == "action-test"
    assert res["param"] == {"content": "Hello", "parameter": "parameters"}


def test_get_actions():
    response = client.get("/v1/action/list")

    # Check that we have at least one config
    result = response.json()
    # TODO: Update it when integrating with action dispatcher
    assert len(result) == 0
