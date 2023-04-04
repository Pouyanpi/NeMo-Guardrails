import pytest
from fastapi.testclient import TestClient

from colangflows.server import api

client = TestClient(api.app)


def test_get():
    response = client.get("/v1/rails/configs")
    assert response.status_code == 200

    # Check that we have at least one config
    result = response.json()
    assert len(result) > 0


@pytest.mark.skip(reason="Should only be run locally as it needs OpenAI key.")
def test_chat_completion():
    response = client.post(
        "/v1/chat/completions",
        json={
            "config_id": "general",
            "messages": [
                {
                    "content": "Hello",
                    "role": "user",
                }
            ],
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert len(res["messages"]) == 1
    assert "NVIDIA" in res["messages"][0]["content"]
