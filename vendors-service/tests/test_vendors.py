import requests
import time

BASE_URL = "http://vendors-service:8003"

def wait_for_service(url, timeout=30):
    for _ in range(timeout):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return
        except requests.ConnectionError:
            time.sleep(1)
    raise Exception(f"Service at {url} not available after {timeout} seconds")

wait_for_service(f"{BASE_URL}/health")

def test_orders_root_available():
    response = requests.get(f"{BASE_URL}/vendors")
    assert response.status_code == 200