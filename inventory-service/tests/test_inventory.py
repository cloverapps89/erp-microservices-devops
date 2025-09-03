import requests

BASE_URL = "http://localhost:8000"

def test_inventory_endpoint_available():
    response = requests.get(f"{BASE_URL}/inventory", headers={"accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert "inventory" in data
    assert isinstance(data["inventory"], list)

def test_inventory_item_structure_if_present():
    response = requests.get(f"{BASE_URL}/inventory", headers={"accept": "application/json"})
    data = response.json()["inventory"]

    if data:  # Only validate structure if data exists
        sample = data[0]
        expected_keys = {"name", "sku", "quantity", "price", "emoji"}
        assert expected_keys.issubset(sample.keys())
