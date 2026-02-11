# GCP GKE Module Variables
# Swiss Engineering Standards: Comprehensive Configuration Management

# Core Configuration
variable "project_id" {
  description = "GCP Project ID for Epic 8 RAG platform"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.project_id))
    error_message = "Project ID must start with a letter, contain only lowercase letters, numbers, and hyphens, and end with a letter or number."
  }
}

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

variable "region" {
  description = "GCP region for deployment (Swiss preference: europe-west6)"
  type        = string
  default     = "europe-west6"

  validation {
    condition     = can(regex("^[a-z]+-[a-z]+[0-9]+$", var.region))
    error_message = "Region must be a valid GCP region format."
  }
}

variable "zones" {
  description = "List of zones for multi-zone deployment. If empty, uses all zones in region"
  type        = list(string)
  default     = []
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
variable "network_name" {
  description = "Name of the VPC network. If empty, creates a new network"
  type        = string
  default     = ""
}

variable "subnet_name" {
  description = "Name of the subnet. If empty, creates a new subnet"
  type        = string
  default     = ""
}

variable "network_cidr" {
  description = "CIDR block for the VPC network"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.network_cidr, 0))
    error_message = "Network CIDR must be a valid IPv4 CIDR block."
  }
}

variable "subnet_cidr" {
  description = "CIDR block for the subnet"
  type        = string
  default     = "10.0.0.0/24"

  validation {
    condition     = can(cidrhost(var.subnet_cidr, 0))
    error_message = "Subnet CIDR must be a valid IPv4 CIDR block."
  }
}

variable "pods_cidr" {
  description = "CIDR block for pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr" {
  description = "CIDR block for services"
  type        = string
  default     = "10.2.0.0/16"
}

variable "enable_private_nodes" {
  description = "Enable private nodes (no public IPs)"
  type        = bool
  default     = true
}

variable "enable_private_endpoint" {
  description = "Enable private cluster endpoint"
  type        = bool
  default     = false
}

variable "master_authorized_networks" {
  description = "List of CIDR blocks for master authorized networks"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = []
}

# GKE Cluster Configuration
variable "kubernetes_version" {
  description = "Kubernetes version prefix for GKE cluster"
  type        = string
  default     = "1.28"

  validation {
    condition     = can(regex("^1\\.(2[6-9]|[3-9][0-9])$", var.kubernetes_version))
    error_message = "Kubernetes version must be 1.26 or higher."
  }
}

variable "release_channel" {
  description = "GKE release channel (UNSPECIFIED, RAPID, REGULAR, STABLE)"
  type        = string
  default     = "STABLE"

  validation {
    condition     = contains(["UNSPECIFIED", "RAPID", "REGULAR", "STABLE"], var.release_channel)
    error_message = "Release channel must be one of: UNSPECIFIED, RAPID, REGULAR, STABLE."
  }
}

variable "remove_default_node_pool" {
  description = "Remove default node pool"
  type        = bool
  default     = true
}

variable "initial_node_count" {
  description = "Initial number of nodes per zone"
  type        = number
  default     = 1

  validation {
    condition     = var.initial_node_count >= 1 && var.initial_node_count <= 10
    error_message = "Initial node count must be between 1 and 10."
  }
}

# Node Pool Configuration
variable "node_pools" {
  description = "GKE node pool configurations"
  type = map(object({
    machine_type    = string
    min_count       = number
    max_count       = number
    initial_count   = number
    disk_size_gb    = number
    disk_type       = string
    preemptible     = bool
    spot            = bool
    auto_repair     = bool
    auto_upgrade    = bool
    max_surge       = number
    max_unavailable = number
    node_labels     = map(string)
    node_taints = list(object({
      key    = string
      value  = string
      effect = string
    }))
    oauth_scopes = list(string)
  }))
  default = {}
}

# Cost Optimization
variable "enable_preemptible_nodes" {
  description = "Enable preemptible nodes for cost optimization"
  type        = bool
  default     = true
}

variable "preemptible_percentage" {
  description = "Percentage of preemptible nodes"
  type        = number
  default     = 50

  validation {
    condition     = var.preemptible_percentage >= 0 && var.preemptible_percentage <= 100
    error_message = "Preemptible percentage must be between 0 and 100."
  }
}

variable "enable_spot_nodes" {
  description = "Enable spot nodes for maximum cost optimization"
  type        = bool
  default     = false
}

# Monitoring and Observability
variable "enable_logging" {
  description = "Enable GKE cluster logging"
  type        = bool
  default     = true
}

variable "logging_components" {
  description = "List of logging components to enable"
  type        = list(string)
  default     = ["SYSTEM_COMPONENTS", "WORKLOADS"]

  validation {
    condition = alltrue([
      for component in var.logging_components :
      contains(["SYSTEM_COMPONENTS", "WORKLOADS", "API_SERVER"], component)
    ])
    error_message = "Logging components must be from: SYSTEM_COMPONENTS, WORKLOADS, API_SERVER."
  }
}

variable "enable_monitoring" {
  description = "Enable GKE cluster monitoring"
  type        = bool
  default     = true
}

variable "monitoring_components" {
  description = "List of monitoring components to enable"
  type        = list(string)
  default     = ["SYSTEM_COMPONENTS", "WORKLOADS"]

  validation {
    condition = alltrue([
      for component in var.monitoring_components :
      contains(["SYSTEM_COMPONENTS", "WORKLOADS", "API_SERVER", "STORAGE", "HPA", "POD"], component)
    ])
    error_message = "Monitoring components must be from: SYSTEM_COMPONENTS, WORKLOADS, API_SERVER, STORAGE, HPA, POD."
  }
}

# Add-ons Configuration
variable "enable_network_policy" {
  description = "Enable network policy (Calico)"
  type        = bool
  default     = true
}

variable "enable_http_load_balancing" {
  description = "Enable HTTP load balancing"
  type        = bool
  default     = true
}

variable "enable_horizontal_pod_autoscaling" {
  description = "Enable horizontal pod autoscaling"
  type        = bool
  default     = true
}

variable "enable_vertical_pod_autoscaling" {
  description = "Enable vertical pod autoscaling"
  type        = bool
  default     = true
}

variable "enable_istio" {
  description = "Enable Istio service mesh"
  type        = bool
  default     = false
}

variable "enable_dns_cache" {
  description = "Enable NodeLocal DNSCache"
  type        = bool
  default     = true
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

# Workload Identity
variable "enable_workload_identity" {
  description = "Enable Workload Identity for secure pod-to-GCP authentication"
  type        = bool
  default     = true
}

variable "workload_identity_namespace" {
  description = "Kubernetes namespace for Workload Identity"
  type        = string
  default     = "epic8"
}

# Binary Authorization
variable "enable_binary_authorization" {
  description = "Enable Binary Authorization for container image security"
  type        = bool
  default     = false
}

# Backup Configuration
variable "enable_backup" {
  description = "Enable GKE Backup for cluster and workload data protection"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention days must be between 1 and 365."
  }
}

# Resource Labeling
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

variable "additional_labels" {
  description = "Additional labels to apply to all resources"
  type        = map(string)
  default     = {}
}

# Maintenance Window
variable "maintenance_window_start_time" {
  description = "Maintenance window start time (RFC3339 format)"
  type        = string
  default     = "2023-01-01T02:00:00Z"
}

variable "maintenance_window_end_time" {
  description = "Maintenance window end time (RFC3339 format)"
  type        = string
  default     = "2023-01-01T06:00:00Z"
}

variable "maintenance_window_recurrence" {
  description = "Maintenance window recurrence (RRULE format)"
  type        = string
  default     = "FREQ=WEEKLY;BYDAY=SA"
}