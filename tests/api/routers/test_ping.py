import pytest

async def test_ping(clinet):
    response = await client.get("/api/v1/ping")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service_name" in data
    assert "version" in data
    assert "services" in data