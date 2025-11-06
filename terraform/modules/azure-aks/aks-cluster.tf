# AKS Cluster Configuration
# Swiss Engineering Standards: High Availability, Security, Monitoring

# Log Analytics Workspace for monitoring (if not provided)
resource "azurerm_log_analytics_workspace" "main" {
  count = var.enable_oms_agent && var.log_analytics_workspace_id == "" ? 1 : 0

  name                = "${local.cluster_name}-logs"
  location            = var.location
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "prod" ? 90 : 30

  tags = merge(local.common_tags, {
    Component = "monitoring"
    Purpose   = "log-analytics"
  })
}

# Key Vault for secrets (maximum security level)
resource "azurerm_key_vault" "main" {
  count = var.security_level == "maximum" ? 1 : 0

  name                = "${replace(local.cluster_name, "-", "")}kv"
  location            = var.location
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Swiss compliance settings
  enabled_for_disk_encryption     = true
  enabled_for_deployment          = true
  enabled_for_template_deployment = true
  purge_protection_enabled        = var.environment == "prod"
  soft_delete_retention_days      = var.environment == "prod" ? 90 : 7

  # Network ACLs for enhanced security
  network_acls {
    bypass                     = "AzureServices"
    default_action             = var.security_level == "maximum" ? "Deny" : "Allow"
    virtual_network_subnet_ids = local.create_subnet ? [azurerm_subnet.aks[0].id] : []
  }

  tags = merge(local.common_tags, {
    Component = "security"
    Purpose   = "secrets-management"
  })
}

# Key Vault access policy for AKS cluster identity
resource "azurerm_key_vault_access_policy" "aks_cluster" {
  count = var.security_level == "maximum" ? 1 : 0

  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_kubernetes_cluster.main.identity[0].principal_id

  secret_permissions = [
    "Get",
    "List"
  ]

  certificate_permissions = [
    "Get",
    "List"
  ]

  key_permissions = [
    "Get",
    "List",
    "Decrypt",
    "Encrypt"
  ]
}

# Disk Encryption Set for customer-managed keys (maximum security)
resource "azurerm_disk_encryption_set" "main" {
  count = var.security_level == "maximum" && var.enable_disk_encryption ? 1 : 0

  name                = "${local.cluster_name}-des"
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  location            = var.location
  key_vault_key_id    = azurerm_key_vault_key.disk_encryption[0].id

  identity {
    type = "SystemAssigned"
  }

  tags = merge(local.common_tags, {
    Component = "security"
    Purpose   = "disk-encryption"
  })
}

# Key Vault Key for disk encryption
resource "azurerm_key_vault_key" "disk_encryption" {
  count = var.security_level == "maximum" && var.enable_disk_encryption ? 1 : 0

  name         = "${local.cluster_name}-disk-encryption-key"
  key_vault_id = azurerm_key_vault.main[0].id
  key_type     = "RSA"
  key_size     = 2048

  key_opts = [
    "decrypt",
    "encrypt",
    "sign",
    "unwrapKey",
    "verify",
    "wrapKey",
  ]

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

# Key Vault access policy for current user (to create keys)
resource "azurerm_key_vault_access_policy" "current_user" {
  count = var.security_level == "maximum" ? 1 : 0

  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  key_permissions = [
    "Create",
    "Delete",
    "Get",
    "List",
    "Update",
    "Decrypt",
    "Encrypt",
    "Sign",
    "UnwrapKey",
    "Verify",
    "WrapKey",
    "Purge",
    "Recover"
  ]

  secret_permissions = [
    "Set",
    "Get",
    "Delete",
    "List",
    "Purge",
    "Recover"
  ]

  certificate_permissions = [
    "Create",
    "Delete",
    "Get",
    "List",
    "Update",
    "Import",
    "Purge",
    "Recover"
  ]
}

# Key Vault access policy for Disk Encryption Set
resource "azurerm_key_vault_access_policy" "disk_encryption_set" {
  count = var.security_level == "maximum" && var.enable_disk_encryption ? 1 : 0

  key_vault_id = azurerm_key_vault.main[0].id
  tenant_id    = azurerm_disk_encryption_set.main[0].identity[0].tenant_id
  object_id    = azurerm_disk_encryption_set.main[0].identity[0].principal_id

  key_permissions = [
    "Get",
    "WrapKey",
    "UnwrapKey"
  ]
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = local.cluster_name
  location            = var.location
  resource_group_name = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
  dns_prefix          = local.cluster_name
  kubernetes_version  = data.azurerm_kubernetes_service_versions.current.latest_version

  # Cluster configuration
  sku_tier                      = var.sku_tier
  automatic_channel_upgrade     = var.automatic_channel_upgrade
  local_account_disabled        = !var.enable_local_account
  private_cluster_enabled       = var.enable_private_cluster
  private_dns_zone_id          = var.enable_private_cluster ? var.private_dns_zone_id : null
  private_cluster_public_fqdn_enabled = var.enable_private_cluster ? false : true

  # Swiss compliance: RBAC and security
  role_based_access_control_enabled = true
  azure_policy_enabled             = var.enable_azure_policy

  # Default node pool
  default_node_pool {
    name                = var.default_node_pool.name
    vm_size             = var.default_node_pool.vm_size
    node_count          = var.default_node_pool.enable_auto_scaling ? null : var.default_node_pool.node_count
    min_count          = var.default_node_pool.enable_auto_scaling ? var.default_node_pool.min_count : null
    max_count          = var.default_node_pool.enable_auto_scaling ? var.default_node_pool.max_count : null
    enable_auto_scaling = var.default_node_pool.enable_auto_scaling
    zones              = var.default_node_pool.availability_zones
    max_pods           = var.default_node_pool.max_pods
    os_disk_size_gb    = var.default_node_pool.os_disk_size_gb
    os_disk_type       = var.default_node_pool.os_disk_type
    vnet_subnet_id     = local.create_subnet ? azurerm_subnet.aks[0].id : data.azurerm_subnet.existing[0].id
    enable_node_public_ip = var.default_node_pool.enable_node_public_ip

    # Pod subnet for Azure CNI
    pod_subnet_id = var.enable_azure_cni && local.create_subnet && var.pod_subnet_address_prefix != "" ? azurerm_subnet.pods[0].id : null

    # Node labels and taints
    node_labels = merge(var.default_node_pool.node_labels, {
      "epic8.io/node-pool"  = var.default_node_pool.name
      "epic8.io/environment" = var.environment
      "epic8.io/managed-by"  = "terraform"
    })

    dynamic "node_taints" {
      for_each = var.default_node_pool.node_taints
      content {
        # node_taints is a list of strings in AKS
      }
    }

    # Security settings
    enable_host_encryption = var.enable_host_encryption

    # Disk encryption
    disk_encryption_set_id = var.security_level == "maximum" && var.enable_disk_encryption ? azurerm_disk_encryption_set.main[0].id : var.disk_encryption_set_id

    # Upgrade settings
    upgrade_settings {
      max_surge = "33%"
    }

    tags = merge(local.common_tags, {
      NodePool = var.default_node_pool.name
      Purpose  = "default-workloads"
    })
  }

  # Cluster identity
  identity {
    type = var.identity_type
  }

  # Network profile
  network_profile {
    network_plugin     = var.network_plugin
    network_policy     = var.network_policy != "" ? var.network_policy : null
    dns_service_ip     = var.dns_service_ip
    service_cidr       = var.service_cidr
    load_balancer_sku  = "standard"
    outbound_type      = var.security_level != "basic" && local.create_subnet ? "userAssignedNATGateway" : "loadBalancer"

    # Load balancer profile for standard SKU
    load_balancer_profile {
      outbound_ip_address_ids = var.security_level != "basic" && local.create_subnet ? [azurerm_public_ip.nat_gateway[0].id] : null
    }
  }

  # Azure AD integration
  dynamic "azure_active_directory_role_based_access_control" {
    for_each = var.enable_azure_rbac ? [1] : []
    content {
      managed                = true
      azure_rbac_enabled     = true
      admin_group_object_ids = var.azure_rbac_admin_group_object_ids
    }
  }

  # OMS Agent (Azure Monitor)
  dynamic "oms_agent" {
    for_each = var.enable_oms_agent ? [1] : []
    content {
      log_analytics_workspace_id = var.log_analytics_workspace_id != "" ? var.log_analytics_workspace_id : azurerm_log_analytics_workspace.main[0].id
    }
  }

  # Microsoft Defender for Containers
  dynamic "microsoft_defender" {
    for_each = var.enable_defender ? [1] : []
    content {
      log_analytics_workspace_id = var.log_analytics_workspace_id != "" ? var.log_analytics_workspace_id : azurerm_log_analytics_workspace.main[0].id
    }
  }

  # Azure Key Vault Secrets Provider
  dynamic "key_vault_secrets_provider" {
    for_each = var.enable_azure_keyvault_secrets_provider ? [1] : []
    content {
      secret_rotation_enabled  = var.secret_rotation_enabled
      secret_rotation_interval = var.secret_rotation_interval
    }
  }

  # Workload Identity (OIDC issuer)
  dynamic "workload_identity_enabled" {
    for_each = var.enable_workload_identity ? [1] : []
    content {}
  }
  oidc_issuer_enabled = var.enable_workload_identity

  # HTTP Application Routing (not recommended for production)
  http_application_routing_enabled = var.enable_http_application_routing

  # Image Cleaner
  image_cleaner_enabled        = var.enable_image_cleaner
  image_cleaner_interval_hours = var.enable_image_cleaner ? 24 : null

  # API Server Access Profile
  dynamic "api_server_access_profile" {
    for_each = !var.enable_private_cluster && length(var.api_server_access_profile.authorized_ip_ranges) > 0 ? [1] : []
    content {
      authorized_ip_ranges = var.api_server_access_profile.authorized_ip_ranges
    }
  }

  # Storage Profile
  storage_profile {
    blob_driver_enabled         = true
    disk_driver_enabled         = true
    file_driver_enabled         = true
    snapshot_controller_enabled = true
  }

  # Auto Scaler Profile
  auto_scaler_profile {
    balance_similar_node_groups      = true
    expander                        = "random"
    max_graceful_termination_sec    = 600
    max_node_provisioning_time      = "15m"
    max_unready_nodes              = 3
    max_unready_percentage         = 45
    new_pod_scale_up_delay         = "10s"
    scale_down_delay_after_add     = "10m"
    scale_down_delay_after_delete  = "10s"
    scale_down_delay_after_failure = "3m"
    scan_interval                  = "10s"
    scale_down_unneeded           = "10m"
    scale_down_utilization_threshold = 0.5
    empty_bulk_delete_max         = 10
    skip_nodes_with_local_storage = false
    skip_nodes_with_system_pods   = true
  }

  # Maintenance Window
  maintenance_window {
    dynamic "allowed" {
      for_each = var.maintenance_window.allowed
      content {
        day   = allowed.value.day
        hours = allowed.value.hours
      }
    }

    dynamic "not_allowed" {
      for_each = var.maintenance_window.not_allowed
      content {
        end   = not_allowed.value.end
        start = not_allowed.value.start
      }
    }
  }

  # Node OS Channel Upgrade
  node_os_channel_upgrade = var.automatic_channel_upgrade != "none" ? "NodeImage" : null

  tags = local.common_tags

  depends_on = [
    azurerm_subnet.aks,
    azurerm_log_analytics_workspace.main,
    azurerm_key_vault.main,
    azurerm_disk_encryption_set.main
  ]

  lifecycle {
    ignore_changes = [
      default_node_pool[0].node_count,
      kubernetes_version,
    ]
  }
}

# Additional Node Pools
resource "azurerm_kubernetes_cluster_node_pool" "additional" {
  for_each = var.additional_node_pools

  name                  = each.key
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size              = each.value.vm_size
  node_count           = each.value.enable_auto_scaling ? null : each.value.node_count
  min_count           = each.value.enable_auto_scaling ? each.value.min_count : null
  max_count           = each.value.enable_auto_scaling ? each.value.max_count : null
  enable_auto_scaling  = each.value.enable_auto_scaling
  zones               = each.value.availability_zones
  max_pods            = each.value.max_pods
  os_disk_size_gb     = each.value.os_disk_size_gb
  os_disk_type        = each.value.os_disk_type
  vnet_subnet_id      = local.create_subnet ? azurerm_subnet.aks[0].id : data.azurerm_subnet.existing[0].id
  enable_node_public_ip = each.value.enable_node_public_ip

  # Pod subnet for Azure CNI
  pod_subnet_id = var.enable_azure_cni && local.create_subnet && var.pod_subnet_address_prefix != "" ? azurerm_subnet.pods[0].id : null

  # Spot instances configuration
  priority        = each.value.priority
  eviction_policy = each.value.priority == "Spot" ? each.value.eviction_policy : null
  spot_max_price  = each.value.priority == "Spot" ? each.value.spot_max_price : null

  # Node labels and taints
  node_labels = merge(each.value.node_labels, {
    "epic8.io/node-pool"  = each.key
    "epic8.io/environment" = var.environment
    "epic8.io/managed-by"  = "terraform"
  })

  node_taints = each.value.node_taints

  # Security settings
  enable_host_encryption = var.enable_host_encryption

  # Disk encryption
  disk_encryption_set_id = var.security_level == "maximum" && var.enable_disk_encryption ? azurerm_disk_encryption_set.main[0].id : var.disk_encryption_set_id

  # Upgrade settings
  upgrade_settings {
    max_surge = "33%"
  }

  tags = merge(local.common_tags, {
    NodePool    = each.key
    Purpose     = lookup(each.value.node_labels, "epic8.io/workload", "additional-workloads")
    Priority    = each.value.priority
    CostOptimized = each.value.priority == "Spot" ? "true" : "false"
  })

  lifecycle {
    ignore_changes = [node_count]
  }
}