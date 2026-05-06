output "app_url" {
  description = "Default hostname of the deployed web app"
  value       = "https://${azurerm_linux_web_app.app.default_hostname}"
}

output "resource_group_name" {
  description = "Resource group containing all resources"
  value       = azurerm_resource_group.rg.name
}
