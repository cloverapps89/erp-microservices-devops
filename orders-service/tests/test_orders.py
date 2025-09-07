import requests
import time

BASE_URL = "http://orders-service:8001"

def wait_for_service(url, timeout=60):
    for _ in range(timeout):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return
        except requests.ConnectionError:
            time.sleep(1)
    raise Exception(f"Service at {url} not available after {timeout} seconds")

wait_for_service(f"{BASE_URL}/health")

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

    # Validate top-level structure
    assert "orders" in data
    assert "inventory" in data
    assert isinstance(data["orders"], list)
    assert isinstance(data["inventory"], list)

    # Validate orders structure if present
    if data["orders"]:
        order = data["orders"][0]
        assert isinstance(order, dict)
        assert "order_number" in order
        assert "customer" in order
        assert "items" in order

    # Validate inventory structure if present
    if data["inventory"]:
        item = data["inventory"][0]
        expected_keys = {"sku", "name", "quantity", "price", "emoji"}
        assert expected_keys.issubset(item.keys())
