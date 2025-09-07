# variable "location" {
#   description = "Azure location"
#   type        = string
#   default     = "eastus"
# }

variable "app_secret" {
  description = "Simulated secret for the app"
  type        = string
  sensitive   = true
}
