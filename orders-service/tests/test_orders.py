import requests

BASE_URL = "http://localhost:8001"

def test_get_orders_html():
    response = requests.get(f"{BASE_URL}/orders/orders-with-inventory")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

def test_get_orders_with_inventory_json():
    response = requests.get(
        f"{BASE_URL}/orders/orders-with-inventory?format=json",
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
    assert any("emoji" in item for item in data["inventory"])
