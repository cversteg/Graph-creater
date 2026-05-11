terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

locals {
  name_suffix = "${var.project}-${var.environment}"
}

resource "azurerm_resource_group" "rg" {
  name     = "${local.name_suffix}-rg"
  location = var.location
}

resource "azurerm_service_plan" "asp" {
  name                = "${local.name_suffix}-asp"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "F1"
}

resource "azurerm_linux_web_app" "app" {
  name                = "${local.name_suffix}-wa"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_service_plan.asp.location
  service_plan_id     = azurerm_service_plan.asp.id
  https_only          = true

  site_config {
    # Always On is not available on free F1 (Basic B1+ only). Enabling it on F1 fails or can force a paid SKU.
    always_on = false

    application_stack {
      python_version = "3.11"
    }

    # Explicit host/port so Oryx/startup matches WEBSITES_PORT (see .streamlit/config.toml).
    app_command_line = "python -m streamlit run app.py --server.port=8000 --server.address=0.0.0.0"
  }

  app_settings = {
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "WEBSITES_PORT"                  = "8000"
  }
}

# Grant the deploying user Owner rights on the resource group
# so cedricverstegen@hotmail.com retains full control.
data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "owner" {
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Owner"
  principal_id         = data.azurerm_client_config.current.object_id
}
