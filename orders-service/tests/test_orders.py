from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient
from main import app
import httpx



client = TestClient(app)

def test_get_orders_html():
    response = client.get("/orders/orders-with-inventory")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

def test_get_orders_with_inventory_json(monkeypatch):
    # Mock the async inventory fetch
    async def mock_get(self, url, **kwargs):  # Accept headers, timeout, etc.
        class MockResponse:
            def raise_for_status(self): pass
            def json(self):
                return {
                        "inventory": [
    {"sku": "APL", "name": "Apples", "quantity": 10, "price": 1.99, "emoji": "🍎"},
    {"sku": "BAN", "name": "Bananas", "quantity": 20, "price": 0.99, "emoji": "🍌"},
    {"sku": "ORG", "name": "Oranges", "quantity": 15, "price": 1.49, "emoji": "🍊"}
]

                }
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    response = client.get(
    "/orders/orders-with-inventory?format=json",
    headers={"Accept": "application/json"}
)

    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")

    data = response.json()

    # Validate orders structure
    assert "orders" in data
    assert isinstance(data["orders"], list)

    if data["orders"]:
        order = data["orders"][0]
        assert isinstance(order, dict)
        assert "order_number" in order
        assert "customer" in order
        assert "items" in order

    # Validate inventory structure
    assert "inventory" in data
    assert isinstance(data["inventory"], list)
    assert any(item["name"] == "Apples" for item in data["inventory"])
