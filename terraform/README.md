# Terraform — Diabetic Retinopathy App

Infrastructure as Code for the Eye ROI Analyzer deployed on Azure.

> ⚠️ The infrastructure is already deployed manually. These Terraform files are for
> documentation, reproducibility, and future re-deployments. Running `terraform apply`
> on existing resources will attempt to import/reconcile them.

## Files

| File | Purpose |
|---|---|
| `main.tf` | All Azure resources defined |
| `variables.tf` | Input variable definitions |
| `outputs.tf` | Output values (URLs, endpoints) |
| `locals.tf` | Shared tags and local values |
| `terraform.tfvars.example` | Example variable values |

## Resources Created

- `azurerm_resource_group` — diabetes-rg (Central India)
- `azurerm_container_registry` — diabetesacr7634 (Basic SKU)
- `azurerm_storage_account` — diabetesstorage19897 (Standard LRS)
- `azurerm_storage_container` — retina-images (public blob)
- `azurerm_log_analytics_workspace` — diabetes-logs
- `azurerm_container_app_environment` — diabetes-env
- `azurerm_container_app` — diabetes-backend (FastAPI + ML)
- `azurerm_static_site` — diabetes-frontend (React)

## Usage

### 1. Install Terraform
```bash
# Windows
winget install HashiCorp.Terraform

# Verify
terraform --version
```

### 2. Setup variables
```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your real values
```

### 3. Initialize
```bash
terraform init
```

### 4. Preview changes (safe — no changes made)
```bash
terraform plan
```

### 5. Apply (creates/updates resources)
```bash
terraform apply
```

### 6. Import existing resources (if already deployed)
```bash
terraform import azurerm_resource_group.main /subscriptions/<sub-id>/resourceGroups/diabetes-rg
terraform import azurerm_container_registry.acr /subscriptions/<sub-id>/resourceGroups/diabetes-rg/providers/Microsoft.ContainerRegistry/registries/diabetesacr7634
terraform import azurerm_storage_account.main /subscriptions/<sub-id>/resourceGroups/diabetes-rg/providers/Microsoft.Storage/storageAccounts/diabetesstorage19897
```

### 7. View outputs
```bash
terraform output
terraform output backend_url
terraform output frontend_url
```

### 8. Destroy all resources (careful!)
```bash
terraform destroy
```

## Important Notes

- `terraform.tfvars` is gitignored — never commit it
- Sensitive outputs (ACR password, SWA token) are marked `sensitive = true`
- The existing deployment is NOT affected by these files unless you run `terraform apply`
