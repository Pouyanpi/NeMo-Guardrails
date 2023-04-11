import pytest
from fastapi.testclient import TestClient

from colangflows.actions_server import actions_server

client = TestClient(actions_server.app)


@pytest.mark.skip(
    reason="Should only be run locally as it fetches data from wikipedia."
)
@pytest.mark.parametrize(
    "action_name, action_parameters, result_field, status",
    [
        (
            "action-test",
            {"content": "Hello", "parameter": "parameters"},
            [],
            "failed",
        ),
        ("Wikipedia", {"query": "president of US?"}, ["text"], "success"),
    ],
)
def test_run(action_name, action_parameters, result_field, status):
    response = client.post(
        "/v1/action/run",
        json={
            "action_name": action_name,
            "action_parameters": action_parameters,
        },
    )

    assert response.status_code == 200
    res = response.json()
    assert list(res["results"].keys()) == result_field
    assert res["status"] == status


def test_get_actions():
    response = client.get("/v1/action/list")

    # Check that we have at least one config
    result = response.json()
    assert len(result) >= 1
