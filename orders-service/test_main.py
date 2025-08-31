from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_orders():
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert isinstance(data["orders"], list)

def test_get_orders_with_inventory(monkeypatch):
    # Mock the call to inventory-service
    def mock_get(url, timeout=5.0):
        class MockResponse:
            def raise_for_status(self): pass
            def json(self): return ["Apples", "Bananas", "Oranges"]
        return MockResponse()

    import httpx
    monkeypatch.setattr(httpx, "get", mock_get)

    response = client.get("/api/orders-with-inventory")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert "inventory" in data
    assert data["orders"] == ["Order1", "Order2", "Order3"]
    assert data["inventory"] == ["Apples", "Bananas", "Oranges"]

