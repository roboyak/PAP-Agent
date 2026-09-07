import asyncio
import json
from uuid import uuid4

import httpx
import httpx2
import pytest
from anthropic import AsyncAnthropic

from pap_agent import agents
from pap_agent.config import Settings


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_cloud_adapter_contract_and_unavailable_result(database, monkeypatch, provider):
    """Exercise the real SDK, create_agent, and schema parser with fake HTTP only."""
    model_name = "gpt-4.1-mini" if provider == "openai" else "claude-haiku-4-5-20251001"
    monkeypatch.setenv("AGENT_BACKEND", provider)
    monkeypatch.setenv("AGENT_MODEL", model_name)
    monkeypatch.setenv(f"{provider.upper()}_API_KEY", "local-test-key")
    assert "local-test-key" not in repr(Settings())
    advice = {
        "evidence_ids": ["evidence-1"],
        "confidence": "keep",
        "fallback": "none",
        "re_evaluate": False,
        "explanation": "Evidence supports the existing guidance.",
        "insufficient": False,
    }
    requests = []
    status = 200

    http = httpx if provider == "openai" else httpx2

    def respond(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert "tools" not in payload or payload["tools"] == []
        assert payload["model"] == model_name
        assert request.url.host == (
            "api.openai.com" if provider == "openai" else "api.anthropic.com"
        )
        if status != 200:
            return http.Response(
                status,
                json={"error": {"message": "sensitive-provider-detail", "type": "api_error"}},
            )
        if provider == "openai":
            assert payload["max_output_tokens"] == 768
            assert payload["store"] is False
            assert payload["text"]["format"]["type"] == "json_schema"
            body = {
                "id": "resp_test",
                "object": "response",
                "created_at": 1,
                "status": "completed",
                "model": model_name,
                "output": [
                    {
                        "type": "message",
                        "id": "msg_test",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {"type": "output_text", "text": json.dumps(advice), "annotations": []}
                        ],
                    }
                ],
                "usage": {
                    "input_tokens": 20,
                    "output_tokens": 30,
                    "total_tokens": 50,
                    "input_tokens_details": {"cached_tokens": 0},
                    "output_tokens_details": {"reasoning_tokens": 0},
                },
            }
        else:
            assert payload["max_tokens"] == 768
            assert payload["output_config"]["format"]["type"] == "json_schema"
            body = {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": model_name,
                "content": [{"type": "text", "text": json.dumps(advice)}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 20, "output_tokens": 30},
            }
        return http.Response(200, json=body)

    transport = http.MockTransport(respond)
    original = agents.ChatOpenAI if provider == "openai" else agents.ChatAnthropic

    def with_fake_http(**kwargs):
        assert kwargs["max_retries"] == 0 and kwargs["timeout"] == 45
        client = http.AsyncClient(transport=transport)
        if provider == "openai":
            return original(**kwargs, http_async_client=client)
        model = original(**kwargs)
        model.__dict__["_async_client"] = AsyncAnthropic(**model._client_params, http_client=client)
        return model

    monkeypatch.setattr(
        agents, "ChatOpenAI" if provider == "openai" else "ChatAnthropic", with_fake_http
    )
    context = {"evidence_id": "evidence-1"}
    record = asyncio.run(
        agents.call_agent(database, uuid4(), uuid4(), "interpretation", context, agents.Advice, {})
    )
    assert record["status"] == "ok"
    assert record["provider"] == provider and record["model"] == model_name
    assert record["output"] == advice
    assert record["usage"]["total_tokens"] == 50
    assert record["tools"] == [] and record["calls"] == 1
    assert "local-test-key" not in json.dumps(record)
    advice["available_kw"] = 999
    invalid = asyncio.run(
        agents.call_agent(database, uuid4(), uuid4(), "interpretation", context, agents.Advice, {})
    )
    assert invalid["status"] == "unavailable" and invalid["output"] is None
    status = 503
    failed = asyncio.run(
        agents.call_agent(database, uuid4(), uuid4(), "interpretation", context, agents.Advice, {})
    )
    assert failed["status"] == "unavailable" and failed["output"] is None
    assert "sensitive-provider-detail" not in json.dumps(failed)
    assert len(requests) == 3  # Exactly one request per reserved attempt, including failure.
