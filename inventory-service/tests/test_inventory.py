import requests

BASE_URL = "http://localhost:8000"

def test_index():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert "Mike's Mystery Machine" in response.text

def test_inventory():
    response = requests.get(f"{BASE_URL}/inventory", headers={"accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert "inventory" in data
    assert isinstance(data["inventory"], list)
    assert len(data["inventory"]) > 0  # Optional: ensure seeded data is present

def test_inventory_item_structure():
    response = requests.get(f"{BASE_URL}/inventory", headers={"accept": "application/json"})
    data = response.json()["inventory"]
    sample = data[0]
    expected_keys = {"name", "sku", "quantity", "price", "emoji"}
    assert expected_keys.issubset(sample.keys())
