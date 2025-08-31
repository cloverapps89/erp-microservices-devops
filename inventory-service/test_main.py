from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Mike's Mystery Machine" in response.text

def test_inventory():
    response = client.get("/api/inventory")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

