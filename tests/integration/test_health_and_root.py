import httpx
import pytest


@pytest.mark.integration
async def test_health_live_endpoint(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.integration
async def test_health_ready_endpoint(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


@pytest.mark.integration
async def test_root_redirects_to_docs(client: httpx.AsyncClient) -> None:
    resp = await client.get("/", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "/docs"


@pytest.mark.integration
async def test_docs_swagger_ui_endpoint(client: httpx.AsyncClient) -> None:
    resp = await client.get("/docs")
    assert resp.status_code == 200
    assert "swagger-ui" in resp.text.lower()


@pytest.mark.integration
async def test_openapi_schema_endpoint(client: httpx.AsyncClient) -> None:
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "openapi" in data
    assert "/api/v1/comments" in data["paths"]
