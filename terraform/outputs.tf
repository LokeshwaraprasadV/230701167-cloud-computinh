# ── Resource Group ─────────────────────────────────────────────────────────────
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

# ── Container Registry ─────────────────────────────────────────────────────────
output "acr_login_server" {
  description = "ACR login server URL"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = azurerm_container_registry.acr.admin_username
  sensitive   = true
}

# ── Storage ────────────────────────────────────────────────────────────────────
output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "blob_container_name" {
  description = "Blob container name for retinal images"
  value       = azurerm_storage_container.retina_images.name
}

output "storage_primary_blob_endpoint" {
  description = "Primary blob storage endpoint"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

# ── Backend ────────────────────────────────────────────────────────────────────
output "backend_url" {
  description = "Backend Container App URL"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "backend_health_url" {
  description = "Backend health check URL"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}/health"
}

# ── Frontend ───────────────────────────────────────────────────────────────────
output "frontend_url" {
  description = "Frontend Static Web App URL"
  value       = "https://${azurerm_static_site.frontend.default_host_name}"
}

output "swa_api_key" {
  description = "Static Web App deployment token (use for CI/CD)"
  value       = azurerm_static_site.frontend.api_key
  sensitive   = true
}
