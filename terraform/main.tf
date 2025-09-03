resource "azurerm_resource_group" "rg" {
  name     = "erp-microservices-rg"
  location = var.location
}

resource "azurerm_storage_account" "sa" {
  name                     = "erpstor${random_id.suffix.hex}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "random_id" "suffix" {
  byte_length = 4
}
