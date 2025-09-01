$env:PYTHONPATH = ".\inventory-service"
pytest inventory-service/tests

$env:PYTHONPATH = ".\orders-service"
pytest orders-service/tests