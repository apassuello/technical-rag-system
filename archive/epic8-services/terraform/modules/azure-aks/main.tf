# Azure AKS Module for Epic 8 Cloud-Native Multi-Model RAG Platform
# Swiss Engineering Standards: Precision, Reliability, Security, Efficiency
# Author: Claude (Terraform Specialist)
# Version: 1.0.0

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.40"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
}

# Configure the Azure Provider
provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Local values for Swiss engineering precision
locals {
  # Swiss region preferences with fallback
  swiss_regions = {
    primary   = "Switzerland North"    # Primary Swiss region
    secondary = "West Europe"          # Amsterdam (EU GDPR compliant)
    tertiary  = "Germany West Central" # Frankfurt (close to Switzerland)
  }

  # Environment-specific resource sizing following Swiss efficiency standards
  environment_configs = {
    dev = {
      vm_size           = "Standard_B2s"
      min_nodes         = 1
      max_nodes         = 3
      initial_nodes     = 2
      spot_percentage   = 80  # Cost optimization
      disk_size         = 64
      enable_autoscaling = true
      availability_zones = ["1", "2"]
    }
    staging = {
      vm_size           = "Standard_D2s_v3"
      min_nodes         = 2
      max_nodes         = 6
      initial_nodes     = 3
      spot_percentage   = 60
      disk_size         = 128
      enable_autoscaling = true
      availability_zones = ["1", "2", "3"]
    }
    prod = {
      vm_size           = "Standard_D4s_v3"
      min_nodes         = 3
      max_nodes         = 12
      initial_nodes     = 6
      spot_percentage   = 40  # Higher reliability for production
      disk_size         = 256
      enable_autoscaling = true
      availability_zones = ["1", "2", "3"]
    }
  }

  # Swiss compliance and security tags
  common_tags = merge(var.additional_tags, {
    Project              = "Epic8-RAG-Platform"
    Environment          = var.environment
    ManagedBy           = "Terraform"
    SwissCompliance     = var.swiss_compliance_enabled ? "enabled" : "disabled"
    DataResidency       = "EU"
    CostCenter          = var.cost_center
    Owner               = var.owner
    SecurityLevel       = var.security_level
    BackupRequired      = "true"
    MonitoringEnabled   = "true"
    ComplianceFramework = "GDPR"
  })

  # AKS cluster name with Swiss naming convention
  cluster_name = "${var.project_name}-${var.environment}-aks-${random_id.cluster_suffix.hex}"

  # Current environment configuration
  current_config = local.environment_configs[var.environment]

  # Resource group name
  resource_group_name = var.resource_group_name != "" ? var.resource_group_name : "${local.cluster_name}-rg"
}

# Random ID for unique cluster naming
resource "random_id" "cluster_suffix" {
  byte_length = 4
}

# Data source for current Azure client configuration
data "azurerm_client_config" "current" {}

# Data source for available zones in the region
data "azurerm_availability_zones" "available" {
  location = var.location
}

# Data source for latest AKS version
data "azurerm_kubernetes_service_versions" "current" {
  location        = var.location
  version_prefix  = var.kubernetes_version
  include_preview = false
}