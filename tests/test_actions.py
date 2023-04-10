import pytest
from fastapi.testclient import TestClient

from colangflows.actions_server import actions_server

client = TestClient(actions_server.app)


@pytest.mark.parametrize(
    "action_name, action_parameters, return_value, events",
    [
        (
            "action-test",
            {"content": "Hello", "parameter": "parameters"},
            type(None),
            [],
        ),
        ("wikipedia", {"query": "president of US?"}, str, []),
    ],
)
def test_run(action_name, action_parameters, return_value, events):
    response = client.post(
        "/v1/action/run",
        json={
            "action_name": action_name,
            "action_parameters": action_parameters,
        },
    )

    assert response.status_code == 200
    res = response.json()
    assert type(res["return_value"]) is return_value
    assert res["events"] == events


def test_get_actions():
    response = client.get("/v1/action/list")

    # Check that we have at least one config
    result = response.json()
    assert len(result) >= 1
