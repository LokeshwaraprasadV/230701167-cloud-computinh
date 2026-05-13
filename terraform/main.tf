terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110.0"
    }
  }

  # Optional: store state in Azure Blob Storage (recommended for teams)
  # backend "azurerm" {
  #   resource_group_name  = "diabetes-rg"
  #   storage_account_name = "<your-state-storage-account>"
  #   container_name       = "tfstate"
  #   key                  = "diabetes.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# ── Resource Group ─────────────────────────────────────────────────────────────
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = local.common_tags
}

# ── Azure Container Registry ───────────────────────────────────────────────────
resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = local.common_tags
}

# ── Storage Account ────────────────────────────────────────────────────────────
resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = local.common_tags
}

# ── Blob Container for retinal images ─────────────────────────────────────────
resource "azurerm_storage_container" "retina_images" {
  name                  = var.blob_container_name
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "blob"
}

# ── Log Analytics Workspace (required by Container Apps) ──────────────────────
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-logs"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = local.common_tags
}

# ── Container Apps Environment ─────────────────────────────────────────────────
resource "azurerm_container_app_environment" "main" {
  name                       = "${var.project_name}-env"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = var.container_apps_location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  tags = local.common_tags
}

# ── Backend Container App ──────────────────────────────────────────────────────
resource "azurerm_container_app" "backend" {
  name                         = "${var.project_name}-backend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
  }

  secret {
    name  = "blob-connection-string"
    value = azurerm_storage_account.main.primary_connection_string
  }

  template {
    min_replicas = 0
    max_replicas = 2

    container {
      name   = "${var.project_name}-backend"
      image  = "${azurerm_container_registry.acr.login_server}/backend:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "MODEL_PATH"
        value = "app/models/dr_model.keras"
      }
      env {
        name  = "REPORTS_DIR"
        value = "storage/reports"
      }
      env {
        name  = "LOCAL_STORAGE_DIR"
        value = "storage"
      }
      env {
        name  = "LOCAL_DB_JSON_PATH"
        value = "storage/db.json"
      }
      env {
        name  = "AZURE_BLOB_CONTAINER_NAME"
        value = var.blob_container_name
      }
      env {
        name        = "AZURE_STORAGE_CONNECTION_STRING"
        secret_name = "blob-connection-string"
      }
      env {
        name  = "FRONTEND_ORIGIN"
        value = "https://${azurerm_static_site.frontend.default_host_name}"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = local.common_tags
}

# ── Static Web App (Frontend) ──────────────────────────────────────────────────
resource "azurerm_static_site" "frontend" {
  name                = "${var.project_name}-frontend"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.static_web_app_location
  sku_tier            = "Free"
  sku_size            = "Free"

  tags = local.common_tags
}
