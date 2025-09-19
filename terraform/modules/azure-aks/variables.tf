# Azure AKS Module Variables
# Swiss Engineering Standards: Comprehensive Configuration Management

# Core Configuration
variable "project_name" {
  description = "Name of the Epic 8 RAG platform project"
  type        = string
  default     = "epic8-rag"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.project_name))
    error_message = "Project name must start with a letter, contain only lowercase letters, numbers, and hyphens, and end with a letter or number."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "location" {
  description = "Azure region for deployment (Swiss preference: Switzerland North)"
  type        = string
  default     = "Switzerland North"

  validation {
    condition = contains([
      "Switzerland North", "Switzerland West", "West Europe",
      "North Europe", "Germany West Central", "France Central"
    ], var.location)
    error_message = "Location must be a valid Azure region, preferably in EU for Swiss compliance."
  }
}

variable "resource_group_name" {
  description = "Name of the resource group. If empty, creates a new resource group"
  type        = string
  default     = ""
}

# Swiss Compliance and Security
variable "swiss_compliance_enabled" {
  description = "Enable Swiss/GDPR compliance configurations"
  type        = bool
  default     = true
}

variable "data_residency_enforcement" {
  description = "Enforce data residency within EU/Swiss regions"
  type        = bool
  default     = true
}

variable "security_level" {
  description = "Security level: basic, enhanced, maximum"
  type        = string
  default     = "enhanced"

  validation {
    condition     = contains(["basic", "enhanced", "maximum"], var.security_level)
    error_message = "Security level must be one of: basic, enhanced, maximum."
  }
}

# Network Configuration
variable "vnet_name" {
  description = "Name of the virtual network. If empty, creates a new VNet"
  type        = string
  default     = ""
}

variable "subnet_name" {
  description = "Name of the subnet. If empty, creates a new subnet"
  type        = string
  default     = ""
}

variable "vnet_address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["10.0.0.0/16"]

  validation {
    condition = alltrue([
      for cidr in var.vnet_address_space : can(cidrhost(cidr, 0))
    ])
    error_message = "All VNet address spaces must be valid IPv4 CIDR blocks."
  }
}

variable "subnet_address_prefix" {
  description = "Address prefix for the AKS subnet"
  type        = string
  default     = "10.0.1.0/24"

  validation {
    condition     = can(cidrhost(var.subnet_address_prefix, 0))
    error_message = "Subnet address prefix must be a valid IPv4 CIDR block."
  }
}

variable "pod_subnet_address_prefix" {
  description = "Address prefix for the pod subnet (CNI)"
  type        = string
  default     = "10.0.2.0/24"
}

variable "service_cidr" {
  description = "CIDR block for Kubernetes services"
  type        = string
  default     = "10.1.0.0/16"
}

variable "dns_service_ip" {
  description = "IP address for the Kubernetes DNS service"
  type        = string
  default     = "10.1.0.10"
}

# AKS Cluster Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for AKS cluster"
  type        = string
  default     = "1.28"

  validation {
    condition     = can(regex("^1\\.(2[6-9]|[3-9][0-9])$", var.kubernetes_version))
    error_message = "Kubernetes version must be 1.26 or higher."
  }
}

variable "automatic_channel_upgrade" {
  description = "Automatic channel upgrade (patch, rapid, node-image, stable)"
  type        = string
  default     = "stable"

  validation {
    condition     = contains(["patch", "rapid", "node-image", "stable", "none"], var.automatic_channel_upgrade)
    error_message = "Automatic channel upgrade must be one of: patch, rapid, node-image, stable, none."
  }
}

variable "sku_tier" {
  description = "SKU tier for AKS cluster (Free, Standard)"
  type        = string
  default     = "Standard"

  validation {
    condition     = contains(["Free", "Standard"], var.sku_tier)
    error_message = "SKU tier must be either Free or Standard."
  }
}

variable "api_server_access_profile" {
  description = "API server access profile configuration"
  type = object({
    authorized_ip_ranges     = list(string)
    subnet_id               = string
    vnet_integration_enabled = bool
  })
  default = {
    authorized_ip_ranges     = []
    subnet_id               = ""
    vnet_integration_enabled = false
  }
}

variable "enable_private_cluster" {
  description = "Enable private cluster (private API server endpoint)"
  type        = bool
  default     = false
}

variable "private_dns_zone_id" {
  description = "Private DNS zone ID for private cluster"
  type        = string
  default     = "System"
}

# Node Pool Configuration
variable "default_node_pool" {
  description = "Default node pool configuration"
  type = object({
    name                = string
    vm_size             = string
    node_count          = number
    min_count          = number
    max_count          = number
    enable_auto_scaling = bool
    availability_zones  = list(string)
    max_pods           = number
    os_disk_size_gb    = number
    os_disk_type       = string
    enable_node_public_ip = bool
    node_labels        = map(string)
    node_taints        = list(string)
  })
  default = {
    name                = "default"
    vm_size             = "Standard_D2s_v3"
    node_count          = 3
    min_count          = 1
    max_count          = 10
    enable_auto_scaling = true
    availability_zones  = ["1", "2", "3"]
    max_pods           = 30
    os_disk_size_gb    = 128
    os_disk_type       = "Managed"
    enable_node_public_ip = false
    node_labels = {
      "epic8.io/node-type" = "default"
    }
    node_taints = []
  }
}

variable "additional_node_pools" {
  description = "Additional node pool configurations"
  type = map(object({
    vm_size             = string
    node_count          = number
    min_count          = number
    max_count          = number
    enable_auto_scaling = bool
    availability_zones  = list(string)
    max_pods           = number
    os_disk_size_gb    = number
    os_disk_type       = string
    enable_node_public_ip = bool
    spot_max_price     = number
    priority           = string
    eviction_policy    = string
    node_labels        = map(string)
    node_taints        = list(string)
  }))
  default = {}
}

# Cost Optimization
variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = true
}

variable "spot_max_price" {
  description = "Maximum price for spot instances (-1 for current on-demand price)"
  type        = number
  default     = -1
}

variable "spot_percentage" {
  description = "Percentage of spot instances in node pools"
  type        = number
  default     = 50

  validation {
    condition     = var.spot_percentage >= 0 && var.spot_percentage <= 100
    error_message = "Spot percentage must be between 0 and 100."
  }
}

# Identity and RBAC
variable "identity_type" {
  description = "Identity type for AKS cluster (SystemAssigned, UserAssigned)"
  type        = string
  default     = "SystemAssigned"

  validation {
    condition     = contains(["SystemAssigned", "UserAssigned"], var.identity_type)
    error_message = "Identity type must be either SystemAssigned or UserAssigned."
  }
}

variable "enable_azure_rbac" {
  description = "Enable Azure RBAC for Kubernetes authorization"
  type        = bool
  default     = true
}

variable "azure_rbac_admin_group_object_ids" {
  description = "List of Azure AD group object IDs for cluster admin access"
  type        = list(string)
  default     = []
}

variable "enable_local_account" {
  description = "Enable local account (not recommended for production)"
  type        = bool
  default     = false
}

# Add-ons Configuration
variable "enable_azure_cni" {
  description = "Enable Azure CNI networking"
  type        = bool
  default     = true
}

variable "network_plugin" {
  description = "Network plugin to use (azure, kubenet)"
  type        = string
  default     = "azure"

  validation {
    condition     = contains(["azure", "kubenet"], var.network_plugin)
    error_message = "Network plugin must be either azure or kubenet."
  }
}

variable "network_policy" {
  description = "Network policy to use (azure, calico)"
  type        = string
  default     = "azure"

  validation {
    condition     = contains(["azure", "calico", ""], var.network_policy)
    error_message = "Network policy must be azure, calico, or empty string."
  }
}

variable "enable_oms_agent" {
  description = "Enable OMS agent for monitoring"
  type        = bool
  default     = true
}

variable "enable_azure_policy" {
  description = "Enable Azure Policy add-on"
  type        = bool
  default     = true
}

variable "enable_http_application_routing" {
  description = "Enable HTTP application routing"
  type        = bool
  default     = false
}

variable "enable_keda" {
  description = "Enable KEDA (Kubernetes Event-driven Autoscaling)"
  type        = bool
  default     = false
}

variable "enable_vertical_pod_autoscaler" {
  description = "Enable Vertical Pod Autoscaler"
  type        = bool
  default     = true
}

variable "enable_workload_identity" {
  description = "Enable Workload Identity"
  type        = bool
  default     = true
}

variable "enable_image_cleaner" {
  description = "Enable image cleaner"
  type        = bool
  default     = true
}

# Security Configuration
variable "enable_host_encryption" {
  description = "Enable host encryption for nodes"
  type        = bool
  default     = false
}

variable "enable_disk_encryption" {
  description = "Enable disk encryption for node OS disks"
  type        = bool
  default     = true
}

variable "disk_encryption_set_id" {
  description = "Disk encryption set ID for customer-managed keys"
  type        = string
  default     = ""
}

variable "enable_azure_keyvault_secrets_provider" {
  description = "Enable Azure Key Vault secrets provider"
  type        = bool
  default     = true
}

variable "secret_rotation_enabled" {
  description = "Enable secret rotation for Key Vault secrets"
  type        = bool
  default     = true
}

variable "secret_rotation_interval" {
  description = "Secret rotation interval"
  type        = string
  default     = "2m"
}

# Epic 8 Platform Configuration
variable "deploy_epic8_platform" {
  description = "Deploy Epic 8 RAG platform via Helm"
  type        = bool
  default     = false
}

variable "epic8_helm_chart_version" {
  description = "Version of Epic 8 Helm chart to deploy"
  type        = string
  default     = "1.0.0"
}

variable "epic8_values_file" {
  description = "Path to Epic 8 Helm values file"
  type        = string
  default     = ""
}

# Monitoring and Logging
variable "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID for monitoring"
  type        = string
  default     = ""
}

variable "enable_defender" {
  description = "Enable Microsoft Defender for Containers"
  type        = bool
  default     = true
}

# Maintenance Window
variable "maintenance_window" {
  description = "Maintenance window configuration"
  type = object({
    allowed = list(object({
      day   = string
      hours = list(number)
    }))
    not_allowed = list(object({
      end   = string
      start = string
    }))
  })
  default = {
    allowed = [{
      day   = "Saturday"
      hours = [2, 3, 4, 5]
    }]
    not_allowed = []
  }
}

# Resource Tagging
variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "platform-team"
}

variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
  default     = "engineering"
}

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}