# output "resource_group_name" {
#   value = azurerm_resource_group.rg.name
# }

# output "storage_account_name" {
#   value = azurerm_storage_account.sa.name
# }

output "app_secret" {
  description = "The generated app secret"
  value       = random_password.app_secret.result
  sensitive   = true
}