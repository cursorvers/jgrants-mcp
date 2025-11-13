from fastapi.testclient import TestClient

from jgrants_mcp_server import app, settings


client = TestClient(app)


def test_health_endpoint() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["api_base_url"] == str(settings.api_base_url)


def test_jgrants_info_returns_config() -> None:
    resp = client.get("/v1/jgrants-info")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["api_base_url"] == str(settings.api_base_url)
    assert payload["jgrants_files_dir"] == settings.jgrants_files_dir
