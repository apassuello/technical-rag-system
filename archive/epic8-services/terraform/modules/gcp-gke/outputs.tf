# GCP GKE Module Outputs
# Swiss Engineering Standards: Comprehensive Information Export

# Cluster Information
output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_id" {
  description = "GKE cluster ID"
  value       = google_container_cluster.primary.id
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint URL"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth.0.cluster_ca_certificate
  sensitive   = true
}

output "cluster_version" {
  description = "GKE cluster Kubernetes version"
  value       = google_container_cluster.primary.master_version
}

output "cluster_location" {
  description = "GKE cluster location (region or zone)"
  value       = google_container_cluster.primary.location
}

output "cluster_zones" {
  description = "List of zones in which the cluster resides"
  value       = google_container_cluster.primary.node_locations
}

# Network Information
output "network_name" {
  description = "VPC network name"
  value       = local.network_name
}

output "network_self_link" {
  description = "VPC network self link"
  value       = local.create_network ? google_compute_network.vpc[0].self_link : data.google_compute_network.existing[0].self_link
}

output "subnet_name" {
  description = "Subnet name"
  value       = local.subnet_name
}

output "subnet_self_link" {
  description = "Subnet self link"
  value       = local.create_subnet ? google_compute_subnetwork.subnet[0].self_link : data.google_compute_subnetwork.existing[0].self_link
}

output "subnet_cidr" {
  description = "Subnet CIDR block"
  value       = local.create_subnet ? google_compute_subnetwork.subnet[0].ip_cidr_range : data.google_compute_subnetwork.existing[0].ip_cidr_range
}

output "pods_cidr" {
  description = "Pods CIDR block"
  value       = var.pods_cidr
}

output "services_cidr" {
  description = "Services CIDR block"
  value       = var.services_cidr
}

# Node Pool Information
output "node_pools" {
  description = "GKE node pools information"
  value = {
    for k, v in google_container_node_pool.pools : k => {
      name           = v.name
      location       = v.location
      node_count     = v.node_count
      machine_type   = v.node_config[0].machine_type
      disk_size_gb   = v.node_config[0].disk_size_gb
      disk_type      = v.node_config[0].disk_type
      preemptible    = v.node_config[0].preemptible
      spot           = v.node_config[0].spot
      oauth_scopes   = v.node_config[0].oauth_scopes
      node_locations = v.node_locations
    }
  }
}

# Service Account Information
output "cluster_service_account_email" {
  description = "GKE cluster service account email"
  value       = google_service_account.gke_cluster.email
}

output "cluster_service_account_name" {
  description = "GKE cluster service account name"
  value       = google_service_account.gke_cluster.name
}

output "node_pool_service_account_email" {
  description = "Node pool service account email"
  value       = google_service_account.gke_nodes.email
}

output "node_pool_service_account_name" {
  description = "Node pool service account name"
  value       = google_service_account.gke_nodes.name
}

# Workload Identity Information
output "workload_identity_enabled" {
  description = "Whether Workload Identity is enabled"
  value       = var.enable_workload_identity
}

output "workload_identity_namespace" {
  description = "Workload Identity namespace"
  value       = var.enable_workload_identity ? var.workload_identity_namespace : null
}

# Swiss Compliance Information
output "swiss_compliance_status" {
  description = "Swiss compliance configuration status"
  value = {
    enabled              = var.swiss_compliance_enabled
    data_residency       = var.data_residency_enforcement
    region               = var.region
    security_level       = var.security_level
    gdpr_compliant      = contains(["europe-west6", "europe-west1", "europe-west3", "europe-west4", "europe-north1"], var.region)
    swiss_region        = var.region == "europe-west6"
  }
}

# Cost Optimization Information
output "cost_optimization" {
  description = "Cost optimization configuration"
  value = {
    preemptible_enabled  = var.enable_preemptible_nodes
    preemptible_percentage = var.preemptible_percentage
    spot_enabled        = var.enable_spot_nodes
    environment         = var.environment
    autoscaling_enabled = local.current_config.enable_autoscaling
  }
}

# Security Information
output "security_configuration" {
  description = "Security configuration details"
  value = {
    private_nodes           = var.enable_private_nodes
    private_endpoint        = var.enable_private_endpoint
    network_policy_enabled  = var.enable_network_policy
    binary_authorization    = var.enable_binary_authorization
    workload_identity      = var.enable_workload_identity
    master_authorized_networks = var.master_authorized_networks
  }
}

# Monitoring Information
output "monitoring_configuration" {
  description = "Monitoring and logging configuration"
  value = {
    logging_enabled      = var.enable_logging
    logging_components   = var.logging_components
    monitoring_enabled   = var.enable_monitoring
    monitoring_components = var.monitoring_components
  }
}

# Epic 8 Platform Information
output "epic8_platform_deployed" {
  description = "Whether Epic 8 platform is deployed"
  value       = var.deploy_epic8_platform
}

output "epic8_helm_release_name" {
  description = "Epic 8 Helm release name"
  value       = var.deploy_epic8_platform ? helm_release.epic8_platform[0].name : null
}

output "epic8_helm_release_status" {
  description = "Epic 8 Helm release status"
  value       = var.deploy_epic8_platform ? helm_release.epic8_platform[0].status : null
}

# Add-ons Information
output "addons_configuration" {
  description = "GKE add-ons configuration"
  value = {
    http_load_balancing          = var.enable_http_load_balancing
    horizontal_pod_autoscaling   = var.enable_horizontal_pod_autoscaling
    vertical_pod_autoscaling     = var.enable_vertical_pod_autoscaling
    network_policy              = var.enable_network_policy
    dns_cache                   = var.enable_dns_cache
    istio                       = var.enable_istio
  }
}

# Backup Information
output "backup_configuration" {
  description = "Backup configuration details"
  value = {
    enabled         = var.enable_backup
    retention_days  = var.backup_retention_days
  }
}

# Connection Information for Epic 8 Services
output "epic8_connection_info" {
  description = "Connection information for Epic 8 services"
  value = {
    cluster_endpoint    = google_container_cluster.primary.endpoint
    region             = var.region
    project_id         = var.project_id
    cluster_name       = google_container_cluster.primary.name
    network_name       = local.network_name
    subnet_name        = local.subnet_name
    zones              = google_container_cluster.primary.node_locations
  }
  sensitive = false
}

# kubeconfig Information
output "kubeconfig_command" {
  description = "Command to get kubeconfig for this cluster"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}"
}

# Resource Labels
output "common_labels" {
  description = "Common labels applied to all resources"
  value       = local.common_labels
}

# Maintenance Window Information
output "maintenance_window" {
  description = "Maintenance window configuration"
  value = {
    start_time  = var.maintenance_window_start_time
    end_time    = var.maintenance_window_end_time
    recurrence  = var.maintenance_window_recurrence
  }
}

# Release Channel Information
output "release_channel" {
  description = "GKE release channel"
  value       = var.release_channel
}

# Cluster Features
output "cluster_features" {
  description = "Enabled cluster features"
  value = {
    autopilot_enabled       = false  # This is a standard GKE cluster
    workload_identity      = var.enable_workload_identity
    binary_authorization   = var.enable_binary_authorization
    network_policy         = var.enable_network_policy
    private_cluster        = var.enable_private_endpoint
    regional_cluster       = true
    multi_zone            = length(data.google_compute_zones.available.names) > 1
  }
}

# Cost Estimation
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (informational)"
  value = {
    cluster_management_fee = "Free for standard GKE"
    node_pool_compute     = "Depends on machine types and count"
    persistent_storage    = "Depends on storage usage"
    load_balancers       = "Depends on ingress configuration"
    network_egress       = "Depends on data transfer"
    note                 = "Use GCP Pricing Calculator for precise estimates"
  }
}