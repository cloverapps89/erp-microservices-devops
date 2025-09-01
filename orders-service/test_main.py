from fastapi.testclient import TestClient
from main import app
import httpx

client = TestClient(app)

def test_get_orders():
    response = client.get("/orders-with-inventory")
    assert response.status_code == 200
    # Could be HTML page if response_class=HTMLResponse
    # So just check the type
    assert "text/html" in response.headers["content-type"]


def test_get_orders_with_inventory(monkeypatch):
    # Mock async inventory call
    async def mock_get(url, timeout=5.0):
        class MockResponse:
            def raise_for_status(self): pass
            def json(self): return {"inventory": ["Apples", "Bananas", "Oranges"]}
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    response = client.get("/api/orders-with-inventory")
    assert response.status_code == 200
    data = response.json()

    # ✅ Assert structure, not exact values
    assert "orders" in data
    assert isinstance(data["orders"], list)

    if data["orders"]:
        order = data["orders"][0]
        assert "order_number" in order
        assert "customer" in order
        assert "items" in order

    assert "inventory" in data
    assert isinstance(data["inventory"], list)
    assert "Apples" in data["inventory"]
