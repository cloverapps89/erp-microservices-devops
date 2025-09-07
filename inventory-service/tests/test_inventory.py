import requests
import time

BASE_URL = "http://inventory-service:8000"

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

def test_inventory_endpoint_available():
    response = requests.get(f"{BASE_URL}/inventory", headers={"accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert "inventory" in data
    assert isinstance(data["inventory"], list)

def test_inventory_item_structure_if_present():
    response = requests.get(f"{BASE_URL}/inventory", headers={"accept": "application/json"})
    data = response.json()["inventory"]

    if data:
        sample = data[0]
        expected_keys = {"name", "sku", "quantity", "price", "emoji"}
        assert expected_keys.issubset(sample.keys())
