# Azure AKS Module Outputs
# Swiss Engineering Standards: Comprehensive Information Export

# Cluster Information
output "cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.main.name
}

output "cluster_id" {
  description = "AKS cluster ID"
  value       = azurerm_kubernetes_cluster.main.id
}

output "cluster_fqdn" {
  description = "AKS cluster FQDN"
  value       = azurerm_kubernetes_cluster.main.fqdn
}

output "cluster_endpoint" {
  description = "AKS cluster API server endpoint"
  value       = azurerm_kubernetes_cluster.main.kube_config.0.host
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "AKS cluster CA certificate"
  value       = azurerm_kubernetes_cluster.main.kube_config.0.cluster_ca_certificate
  sensitive   = true
}

output "cluster_version" {
  description = "AKS cluster Kubernetes version"
  value       = azurerm_kubernetes_cluster.main.kubernetes_version
}

output "cluster_location" {
  description = "AKS cluster location"
  value       = azurerm_kubernetes_cluster.main.location
}

# Identity Information
output "cluster_identity" {
  description = "AKS cluster identity"
  value = {
    type         = azurerm_kubernetes_cluster.main.identity[0].type
    principal_id = azurerm_kubernetes_cluster.main.identity[0].principal_id
    tenant_id    = azurerm_kubernetes_cluster.main.identity[0].tenant_id
  }
}

output "kubelet_identity" {
  description = "AKS kubelet identity"
  value = {
    client_id                 = azurerm_kubernetes_cluster.main.kubelet_identity[0].client_id
    object_id                 = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
    user_assigned_identity_id = azurerm_kubernetes_cluster.main.kubelet_identity[0].user_assigned_identity_id
  }
}

# Network Information
output "resource_group_name" {
  description = "Resource group name"
  value       = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
}

output "resource_group_id" {
  description = "Resource group ID"
  value       = local.create_resource_group ? azurerm_resource_group.main[0].id : data.azurerm_resource_group.existing[0].id
}

output "vnet_name" {
  description = "Virtual network name"
  value       = local.vnet_name
}

output "vnet_id" {
  description = "Virtual network ID"
  value       = local.create_vnet ? azurerm_virtual_network.main[0].id : data.azurerm_virtual_network.existing[0].id
}

output "subnet_name" {
  description = "AKS subnet name"
  value       = local.subnet_name
}

output "subnet_id" {
  description = "AKS subnet ID"
  value       = local.create_subnet ? azurerm_subnet.aks[0].id : data.azurerm_subnet.existing[0].id
}

output "subnet_address_prefix" {
  description = "AKS subnet address prefix"
  value       = var.subnet_address_prefix
}

output "service_cidr" {
  description = "Kubernetes service CIDR"
  value       = var.service_cidr
}

output "dns_service_ip" {
  description = "Kubernetes DNS service IP"
  value       = var.dns_service_ip
}

# Node Pool Information
output "default_node_pool" {
  description = "Default node pool information"
  value = {
    name                = azurerm_kubernetes_cluster.main.default_node_pool[0].name
    vm_size             = azurerm_kubernetes_cluster.main.default_node_pool[0].vm_size
    node_count          = azurerm_kubernetes_cluster.main.default_node_pool[0].node_count
    max_pods           = azurerm_kubernetes_cluster.main.default_node_pool[0].max_pods
    os_disk_size_gb    = azurerm_kubernetes_cluster.main.default_node_pool[0].os_disk_size_gb
    availability_zones  = azurerm_kubernetes_cluster.main.default_node_pool[0].zones
  }
}

output "additional_node_pools" {
  description = "Additional node pools information"
  value = {
    for k, v in azurerm_kubernetes_cluster_node_pool.additional : k => {
      name                = v.name
      vm_size             = v.vm_size
      node_count          = v.node_count
      min_count          = v.min_count
      max_count          = v.max_count
      max_pods           = v.max_pods
      os_disk_size_gb    = v.os_disk_size_gb
      availability_zones  = v.zones
      priority           = v.priority
      spot_max_price     = v.spot_max_price
    }
  }
}

# Monitoring Information
output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  value       = var.enable_oms_agent ? (var.log_analytics_workspace_id != "" ? var.log_analytics_workspace_id : azurerm_log_analytics_workspace.main[0].id) : null
}

output "oms_agent_addon" {
  description = "OMS agent addon configuration"
  value       = var.enable_oms_agent ? azurerm_kubernetes_cluster.main.oms_agent[0] : null
}

# Swiss Compliance Information
output "swiss_compliance_status" {
  description = "Swiss compliance configuration status"
  value = {
    enabled              = var.swiss_compliance_enabled
    data_residency       = var.data_residency_enforcement
    location             = var.location
    security_level       = var.security_level
    gdpr_compliant      = contains(["Switzerland North", "Switzerland West", "West Europe", "North Europe", "Germany West Central", "France Central"], var.location)
    swiss_region        = contains(["Switzerland North", "Switzerland West"], var.location)
  }
}

# Cost Optimization Information
output "cost_optimization" {
  description = "Cost optimization configuration"
  value = {
    spot_instances_enabled = var.enable_spot_instances
    spot_percentage       = var.spot_percentage
    spot_max_price       = var.spot_max_price
    environment          = var.environment
    sku_tier            = var.sku_tier
  }
}

# Security Information
output "security_configuration" {
  description = "Security configuration details"
  value = {
    private_cluster              = var.enable_private_cluster
    azure_rbac_enabled          = var.enable_azure_rbac
    local_account_disabled      = !var.enable_local_account
    workload_identity_enabled   = var.enable_workload_identity
    azure_policy_enabled       = var.enable_azure_policy
    defender_enabled           = var.enable_defender
    host_encryption_enabled    = var.enable_host_encryption
    disk_encryption_enabled    = var.enable_disk_encryption
    keyvault_secrets_provider  = var.enable_azure_keyvault_secrets_provider
    network_policy            = var.network_policy
  }
}

# Add-ons Information
output "addons_configuration" {
  description = "AKS add-ons configuration"
  value = {
    oms_agent                    = var.enable_oms_agent
    azure_policy                = var.enable_azure_policy
    http_application_routing     = var.enable_http_application_routing
    keda                        = var.enable_keda
    vertical_pod_autoscaler     = var.enable_vertical_pod_autoscaler
    workload_identity          = var.enable_workload_identity
    image_cleaner              = var.enable_image_cleaner
    azure_keyvault_secrets_provider = var.enable_azure_keyvault_secrets_provider
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

# Key Vault Information (if created)
output "key_vault_id" {
  description = "Key Vault ID for secrets"
  value       = var.security_level == "maximum" ? azurerm_key_vault.main[0].id : null
}

output "key_vault_name" {
  description = "Key Vault name for secrets"
  value       = var.security_level == "maximum" ? azurerm_key_vault.main[0].name : null
}

# Connection Information for Epic 8 Services
output "epic8_connection_info" {
  description = "Connection information for Epic 8 services"
  value = {
    cluster_endpoint    = azurerm_kubernetes_cluster.main.kube_config.0.host
    location           = var.location
    resource_group     = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
    cluster_name       = azurerm_kubernetes_cluster.main.name
    vnet_name          = local.vnet_name
    subnet_name        = local.subnet_name
  }
  sensitive = false
}

# kubeconfig Information
output "kubeconfig_command" {
  description = "Command to get kubeconfig for this cluster"
  value = "az aks get-credentials --resource-group ${local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name} --name ${azurerm_kubernetes_cluster.main.name}"
}

output "kube_config" {
  description = "Raw kubeconfig for the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}

# Resource Tags
output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# Network Security Group Information
output "nsg_id" {
  description = "Network Security Group ID"
  value       = var.security_level != "basic" ? azurerm_network_security_group.aks[0].id : null
}

output "nsg_name" {
  description = "Network Security Group name"
  value       = var.security_level != "basic" ? azurerm_network_security_group.aks[0].name : null
}

# Load Balancer Information
output "load_balancer_sku" {
  description = "Load balancer SKU"
  value       = azurerm_kubernetes_cluster.main.network_profile[0].load_balancer_sku
}

# OIDC Issuer Information
output "oidc_issuer_url" {
  description = "OIDC issuer URL"
  value       = var.enable_workload_identity ? azurerm_kubernetes_cluster.main.oidc_issuer_url : null
}

# Cluster Features
output "cluster_features" {
  description = "Enabled cluster features"
  value = {
    automatic_channel_upgrade = azurerm_kubernetes_cluster.main.automatic_channel_upgrade
    azure_cni_enabled        = var.enable_azure_cni
    private_cluster         = var.enable_private_cluster
    workload_identity       = var.enable_workload_identity
    azure_rbac             = var.enable_azure_rbac
    network_policy         = var.network_policy
    sku_tier               = azurerm_kubernetes_cluster.main.sku_tier
  }
}

# Maintenance Window Information
output "maintenance_window" {
  description = "Maintenance window configuration"
  value       = var.maintenance_window
}

# Cost Estimation
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (informational)"
  value = {
    cluster_management_fee = var.sku_tier == "Standard" ? "Charged based on cluster uptime" : "Free"
    node_pool_compute     = "Depends on VM sizes and count"
    persistent_storage    = "Depends on storage usage"
    load_balancers       = "Standard Load Balancer charges apply"
    network_egress       = "Depends on data transfer"
    log_analytics        = var.enable_oms_agent ? "Depends on log ingestion volume" : "None"
    note                 = "Use Azure Pricing Calculator for precise estimates"
  }
}

# Availability Zones Information
output "availability_zones" {
  description = "Available zones in the region"
  value       = data.azurerm_availability_zones.available.names
}

# API Server Access Profile
output "api_server_access_profile" {
  description = "API server access profile configuration"
  value = var.enable_private_cluster ? {
    private_cluster_enabled = true
    private_dns_zone_id    = var.private_dns_zone_id
  } : {
    authorized_ip_ranges = var.api_server_access_profile.authorized_ip_ranges
  }
}