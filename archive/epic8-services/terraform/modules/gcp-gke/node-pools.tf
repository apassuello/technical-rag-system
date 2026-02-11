# GKE Node Pools Configuration
# Swiss Engineering Standards: Cost-Optimized, High-Performance, Reliable

# Local values for node pool configurations
locals {
  # Default node pools if none specified
  default_node_pools = {
    # General purpose node pool
    general = {
      machine_type    = local.current_config.machine_types[0]
      min_count       = local.current_config.min_nodes
      max_count       = local.current_config.max_nodes
      initial_count   = local.current_config.initial_nodes
      disk_size_gb    = local.current_config.disk_size
      disk_type       = "pd-standard"
      preemptible     = var.enable_preemptible_nodes && local.current_config.preemptible_ratio > 0.5
      spot            = var.enable_spot_nodes
      auto_repair     = true
      auto_upgrade    = true
      max_surge       = 1
      max_unavailable = 0
      node_labels = {
        "epic8.io/node-type"    = "general"
        "epic8.io/workload"     = "api-services"
        "epic8.io/environment"  = var.environment
      }
      node_taints = []
      oauth_scopes = [
        "https://www.googleapis.com/auth/cloud-platform"
      ]
    }

    # High-memory node pool for ML workloads
    ml-workloads = {
      machine_type    = var.environment == "prod" ? "n1-highmem-4" : "n1-highmem-2"
      min_count       = var.environment == "prod" ? 1 : 0
      max_count       = var.environment == "prod" ? 6 : 3
      initial_count   = var.environment == "prod" ? 2 : 1
      disk_size_gb    = 200
      disk_type       = "pd-ssd"
      preemptible     = false  # Critical ML workloads need stability
      spot            = false
      auto_repair     = true
      auto_upgrade    = true
      max_surge       = 1
      max_unavailable = 0
      node_labels = {
        "epic8.io/node-type"    = "ml-workloads"
        "epic8.io/high-memory"  = "true"
        "epic8.io/gpu-ready"    = "false"
        "workload.epic8.io/ml"  = "true"
      }
      node_taints = [{
        key    = "workload.epic8.io/ml"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
      oauth_scopes = [
        "https://www.googleapis.com/auth/cloud-platform"
      ]
    }

    # Preemptible node pool for cost optimization
    preemptible-workloads = var.enable_preemptible_nodes ? {
      machine_type    = local.current_config.machine_types[0]
      min_count       = 0
      max_count       = local.current_config.max_nodes
      initial_count   = 0
      disk_size_gb    = local.current_config.disk_size
      disk_type       = "pd-standard"
      preemptible     = true
      spot            = var.enable_spot_nodes
      auto_repair     = true
      auto_upgrade    = true
      max_surge       = 2
      max_unavailable = 1
      node_labels = {
        "epic8.io/node-type"        = "preemptible"
        "epic8.io/cost-optimized"   = "true"
        "cloud.google.com/gke-preemptible" = "true"
      }
      node_taints = [{
        key    = "epic8.io/preemptible"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
      oauth_scopes = [
        "https://www.googleapis.com/auth/cloud-platform"
      ]
    } : {}
  }

  # Use provided node pools or default ones
  node_pools = length(var.node_pools) > 0 ? var.node_pools : local.default_node_pools
}

# Node Pools
resource "google_container_node_pool" "pools" {
  for_each = local.node_pools

  name       = each.key
  location   = var.region
  cluster    = google_container_cluster.primary.name

  # Autoscaling configuration
  dynamic "autoscaling" {
    for_each = local.current_config.enable_autoscaling ? [1] : []
    content {
      min_node_count = each.value.min_count
      max_node_count = each.value.max_count
    }
  }

  # Initial node count
  initial_node_count = each.value.initial_count

  # Upgrade settings for Swiss reliability standards
  upgrade_settings {
    max_surge       = each.value.max_surge
    max_unavailable = each.value.max_unavailable
    strategy        = "SURGE"

    # Blue-green upgrade settings for production
    dynamic "blue_green_settings" {
      for_each = var.environment == "prod" ? [1] : []
      content {
        standard_rollout_policy {
          batch_percentage    = 25.0
          batch_node_count    = 1
          batch_soak_duration = "60s"
        }
        node_pool_soak_duration = "300s"
      }
    }
  }

  # Management configuration
  management {
    auto_repair  = each.value.auto_repair
    auto_upgrade = each.value.auto_upgrade
  }

  # Node configuration
  node_config {
    preemptible  = each.value.preemptible
    spot         = each.value.spot
    machine_type = each.value.machine_type
    disk_size_gb = each.value.disk_size_gb
    disk_type    = each.value.disk_type

    # Service account
    service_account = google_service_account.gke_nodes.email
    oauth_scopes    = each.value.oauth_scopes

    # Node labels
    labels = merge(each.value.node_labels, local.common_labels, {
      "epic8.io/node-pool"  = each.key
      "epic8.io/managed-by" = "terraform"
    })

    # Node taints
    dynamic "taint" {
      for_each = each.value.node_taints
      content {
        key    = taint.value.key
        value  = taint.value.value
        effect = taint.value.effect
      }
    }

    # Network tags
    tags = ["gke-node", "epic8-node", "${local.cluster_name}-${each.key}"]

    # Security configurations
    shielded_instance_config {
      enable_secure_boot          = var.security_level != "basic"
      enable_integrity_monitoring = var.security_level != "basic"
    }

    # Workload metadata configuration for Workload Identity
    workload_metadata_config {
      mode = var.enable_workload_identity ? "GKE_METADATA" : "GCE_METADATA"
    }

    # Metadata for enhanced security
    metadata = {
      disable-legacy-endpoints = "true"
      google-compute-enable-pcid = "true"
    }

    # Image type selection based on security level
    image_type = var.security_level == "maximum" ? "COS_CONTAINERD" : "COS_CONTAINERD"

    # Local SSD configuration for high-performance workloads
    dynamic "local_ssd_config" {
      for_each = each.key == "ml-workloads" && var.environment == "prod" ? [1] : []
      content {
        count = 1
      }
    }

    # Ephemeral storage configuration
    dynamic "ephemeral_storage_config" {
      for_each = each.key == "ml-workloads" ? [1] : []
      content {
        local_ssd_count = 1
      }
    }

    # Resource management
    resource_labels = merge(local.common_labels, {
      "epic8.io/node-pool" = each.key
      "epic8.io/workload-type" = lookup(each.value.node_labels, "epic8.io/workload", "general")
    })

    # Boot disk encryption (enhanced security and above)
    dynamic "gcfs_config" {
      for_each = var.security_level != "basic" ? [1] : []
      content {
        enabled = true
      }
    }

    # Guest accelerator (GPU) configuration for ML workloads
    dynamic "guest_accelerator" {
      for_each = each.key == "ml-workloads" && var.environment == "prod" ? [
        {
          type  = "nvidia-tesla-t4"
          count = 1
        }
      ] : []
      content {
        type  = guest_accelerator.value.type
        count = guest_accelerator.value.count
        gpu_partition_size = null

        gpu_sharing_config {
          gpu_sharing_strategy       = "TIME_SHARING"
          max_shared_clients_per_gpu = 2
        }

        gpu_driver_installation_config {
          gpu_driver_version = "DEFAULT"
        }
      }
    }

    # Advanced machine configuration for specific workloads
    dynamic "advanced_machine_features" {
      for_each = each.key == "ml-workloads" ? [1] : []
      content {
        threads_per_core = 1
        enable_nested_virtualization = false
      }
    }

    # Reservation affinity for cost optimization
    dynamic "reservation_affinity" {
      for_each = var.environment == "prod" && each.key == "general" ? [1] : []
      content {
        consume_reservation_type = "ANY_RESERVATION"
      }
    }
  }

  # Network configuration for multi-zone deployment
  node_locations = length(var.zones) > 0 ? var.zones : null

  # Placement policy for Swiss efficiency standards
  dynamic "placement_policy" {
    for_each = each.key == "ml-workloads" && var.environment == "prod" ? [1] : []
    content {
      type = "COMPACT"
    }
  }

  # Network performance configuration
  dynamic "network_config" {
    for_each = each.key == "ml-workloads" ? [1] : []
    content {
      create_pod_range     = false
      enable_private_nodes = var.enable_private_nodes

      dynamic "pod_cidr_overprovision_config" {
        for_each = var.environment == "prod" ? [1] : []
        content {
          disabled = false
        }
      }
    }
  }

  # Lifecycle management
  lifecycle {
    ignore_changes = [initial_node_count]
  }

  depends_on = [
    google_service_account.gke_nodes,
    google_project_iam_member.gke_nodes,
  ]

  timeouts {
    create = "30m"
    update = "30m"
    delete = "30m"
  }
}

# Node pool for GPU workloads (conditional - only for production ML)
resource "google_container_node_pool" "gpu_pool" {
  count = var.environment == "prod" && contains(keys(local.node_pools), "ml-workloads") ? 1 : 0

  name       = "gpu-workloads"
  location   = var.region
  cluster    = google_container_cluster.primary.name

  initial_node_count = 0

  autoscaling {
    min_node_count = 0
    max_node_count = 2
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
    strategy        = "SURGE"
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    preemptible  = false
    spot         = false
    machine_type = "n1-standard-4"
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = merge(local.common_labels, {
      "epic8.io/node-type"    = "gpu-workloads"
      "epic8.io/gpu-enabled"  = "true"
      "epic8.io/workload"     = "ml-inference"
      "epic8.io/node-pool"    = "gpu-workloads"
    })

    taint {
      key    = "epic8.io/gpu"
      value  = "true"
      effect = "NO_SCHEDULE"
    }

    tags = ["gke-node", "epic8-node", "gpu-node"]

    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
      gpu_partition_size = null

      gpu_sharing_config {
        gpu_sharing_strategy       = "TIME_SHARING"
        max_shared_clients_per_gpu = 4
      }

      gpu_driver_installation_config {
        gpu_driver_version = "DEFAULT"
      }
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    metadata = {
      disable-legacy-endpoints = "true"
    }

    resource_labels = merge(local.common_labels, {
      "epic8.io/node-pool" = "gpu-workloads"
      "epic8.io/gpu-type"  = "nvidia-tesla-t4"
    })
  }

  # Only deploy in zones that support GPUs
  node_locations = ["${var.region}-a", "${var.region}-b"]

  depends_on = [
    google_service_account.gke_nodes,
    google_project_iam_member.gke_nodes,
  ]

  timeouts {
    create = "30m"
    update = "30m"
    delete = "30m"
  }
}