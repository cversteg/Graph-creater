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

  site_config {
    always_on = false  # F1 tier does not support always_on

    application_stack {
      python_version = "3.11"
    }

    app_command_line = "streamlit run app.py"
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
