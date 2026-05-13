variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  # Set via: export TF_VAR_subscription_id="your-subscription-id"
  # or in terraform.tfvars
}

variable "project_name" {
  description = "Base name for all resources"
  type        = string
  default     = "diabetes"
}

variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "diabetes-rg"
}

variable "location" {
  description = "Primary Azure region for most resources"
  type        = string
  default     = "centralindia"
}

variable "container_apps_location" {
  description = "Azure region for Container Apps (must support the service)"
  type        = string
  default     = "centralindia"
}

variable "static_web_app_location" {
  description = "Azure region for Static Web Apps (limited regions available)"
  type        = string
  default     = "eastasia"
}

variable "acr_name" {
  description = "Name of the Azure Container Registry (must be globally unique)"
  type        = string
  default     = "diabetesacr7634"
}

variable "storage_account_name" {
  description = "Name of the Azure Storage Account (must be globally unique, 3-24 lowercase chars)"
  type        = string
  default     = "diabetesstorage19897"
}

variable "blob_container_name" {
  description = "Name of the blob container for retinal images"
  type        = string
  default     = "retina-images"
}
