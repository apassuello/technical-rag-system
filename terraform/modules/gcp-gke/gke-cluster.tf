# GKE Cluster Configuration
# Swiss Engineering Standards: High Availability, Security, Monitoring

# Service Account for GKE Cluster
resource "google_service_account" "gke_cluster" {
  account_id   = "${local.cluster_name}-cluster-sa"
  display_name = "GKE Cluster Service Account for ${local.cluster_name}"
  description  = "Service account for Epic 8 GKE cluster operations"
}

# IAM bindings for cluster service account
resource "google_project_iam_member" "gke_cluster" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/stackdriver.resourceMetadata.writer",
    "roles/monitoring.dashboardEditor"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_cluster.email}"
}

# Additional IAM for Workload Identity (if enabled)
resource "google_service_account_iam_member" "workload_identity" {
  count = var.enable_workload_identity ? 1 : 0

  service_account_id = google_service_account.gke_cluster.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.workload_identity_namespace}/epic8-workload-identity]"
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = local.cluster_name
  location = var.region

  # Node configuration
  remove_default_node_pool = var.remove_default_node_pool
  initial_node_count       = var.remove_default_node_pool ? null : var.initial_node_count

  # Network configuration
  network    = local.create_network ? google_compute_network.vpc[0].self_link : data.google_compute_network.existing[0].self_link
  subnetwork = local.create_subnet ? google_compute_subnetwork.subnet[0].self_link : data.google_compute_subnetwork.existing[0].self_link

  # IP allocation policy for secondary ranges
  ip_allocation_policy {
    cluster_secondary_range_name  = "${local.cluster_name}-pods"
    services_secondary_range_name = "${local.cluster_name}-services"
  }

  # Private cluster configuration for Swiss security standards
  private_cluster_config {
    enable_private_nodes    = var.enable_private_nodes
    enable_private_endpoint = var.enable_private_endpoint
    master_ipv4_cidr_block  = var.enable_private_endpoint ? "172.16.0.0/28" : null

    master_global_access_config {
      enabled = var.security_level == "maximum" ? false : true
    }
  }

  # Master authorized networks for enhanced security
  dynamic "master_authorized_networks_config" {
    for_each = length(var.master_authorized_networks) > 0 ? [1] : []
    content {
      dynamic "cidr_blocks" {
        for_each = var.master_authorized_networks
        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }

  # Kubernetes version and release channel
  min_master_version = data.google_container_engine_versions.gke_version.latest_master_version

  release_channel {
    channel = var.release_channel
  }

  # Workload Identity for secure GCP integration
  dynamic "workload_identity_config" {
    for_each = var.enable_workload_identity ? [1] : []
    content {
      workload_pool = "${var.project_id}.svc.id.goog"
    }
  }

  # Add-ons configuration
  addons_config {
    http_load_balancing {
      disabled = !var.enable_http_load_balancing
    }

    horizontal_pod_autoscaling {
      disabled = !var.enable_horizontal_pod_autoscaling
    }

    network_policy_config {
      disabled = !var.enable_network_policy
    }

    dns_cache_config {
      enabled = var.enable_dns_cache
    }

    # GCE Persistent Disk CSI Driver
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }

    # Istio service mesh (if enabled)
    dynamic "istio_config" {
      for_each = var.enable_istio ? [1] : []
      content {
        disabled = false
        auth     = "AUTH_MUTUAL_TLS"
      }
    }
  }

  # Network policy for micro-segmentation
  dynamic "network_policy" {
    for_each = var.enable_network_policy ? [1] : []
    content {
      enabled  = true
      provider = "CALICO"
    }
  }

  # Binary Authorization for container security (maximum security)
  dynamic "binary_authorization" {
    for_each = var.enable_binary_authorization ? [1] : []
    content {
      evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
    }
  }

  # Logging configuration
  logging_config {
    enable_components = var.enable_logging ? var.logging_components : []
  }

  # Monitoring configuration
  monitoring_config {
    enable_components = var.enable_monitoring ? var.monitoring_components : []

    # Managed Prometheus (enhanced security and above)
    dynamic "managed_prometheus" {
      for_each = var.enable_monitoring && var.security_level != "basic" ? [1] : []
      content {
        enabled = true
      }
    }
  }

  # Cluster maintenance policy
  maintenance_policy {
    recurring_window {
      start_time = var.maintenance_window_start_time
      end_time   = var.maintenance_window_end_time
      recurrence = var.maintenance_window_recurrence
    }
  }

  # Node pool defaults (if not removing default pool)
  dynamic "node_config" {
    for_each = var.remove_default_node_pool ? [] : [1]
    content {
      preemptible  = var.enable_preemptible_nodes
      machine_type = local.current_config.machine_types[0]
      disk_size_gb = local.current_config.disk_size
      disk_type    = "pd-standard"

      # Service account for nodes
      service_account = google_service_account.gke_nodes.email
      oauth_scopes = [
        "https://www.googleapis.com/auth/cloud-platform"
      ]

      # Metadata and labels
      labels = merge(local.common_labels, {
        "epic8.io/node-pool" = "default"
        "epic8.io/managed-by" = "terraform"
      })

      tags = ["gke-node", "epic8-node"]

      # Security configurations
      shielded_instance_config {
        enable_secure_boot          = var.security_level != "basic"
        enable_integrity_monitoring = var.security_level != "basic"
      }

      # Workload metadata configuration
      workload_metadata_config {
        mode = var.enable_workload_identity ? "GKE_METADATA" : "GCE_METADATA"
      }
    }
  }

  # Vertical Pod Autoscaling
  dynamic "vertical_pod_autoscaling" {
    for_each = var.enable_vertical_pod_autoscaling ? [1] : []
    content {
      enabled = true
    }
  }

  # Cost management configuration
  cost_management_config {
    enabled = var.environment == "prod" ? true : false
  }

  # Notification configuration for Swiss compliance
  notification_config {
    pubsub {
      enabled = var.swiss_compliance_enabled
      topic   = var.swiss_compliance_enabled ? google_pubsub_topic.gke_notifications[0].id : null
    }
  }

  # Database encryption for maximum security
  dynamic "database_encryption" {
    for_each = var.security_level == "maximum" ? [1] : []
    content {
      state    = "ENCRYPTED"
      key_name = google_kms_crypto_key.gke_encryption[0].id
    }
  }

  # Labels for resource management
  resource_labels = local.common_labels

  # Lifecycle management
  lifecycle {
    ignore_changes = [node_config]
  }

  depends_on = [
    google_project_iam_member.gke_cluster,
  ]
}

# Service Account for Node Pools
resource "google_service_account" "gke_nodes" {
  account_id   = "${local.cluster_name}-nodes-sa"
  display_name = "GKE Node Pool Service Account for ${local.cluster_name}"
  description  = "Service account for Epic 8 GKE node pools"
}

# IAM bindings for node service account
resource "google_project_iam_member" "gke_nodes" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer",
    "roles/storage.objectViewer"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

# Pub/Sub topic for cluster notifications (Swiss compliance)
resource "google_pubsub_topic" "gke_notifications" {
  count = var.swiss_compliance_enabled ? 1 : 0

  name = "${local.cluster_name}-notifications"

  labels = merge(local.common_labels, {
    component = "monitoring"
    purpose   = "cluster-notifications"
  })

  message_retention_duration = "604800s" # 7 days
}

# KMS key for cluster encryption (maximum security)
resource "google_kms_key_ring" "gke" {
  count = var.security_level == "maximum" ? 1 : 0

  name     = "${local.cluster_name}-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "gke_encryption" {
  count = var.security_level == "maximum" ? 1 : 0

  name     = "${local.cluster_name}-encryption-key"
  key_ring = google_kms_key_ring.gke[0].id
  purpose  = "ENCRYPT_DECRYPT"

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }

  rotation_period = "7776000s" # 90 days

  labels = merge(local.common_labels, {
    component = "security"
    purpose   = "cluster-encryption"
  })
}

# IAM binding for GKE to use the encryption key
resource "google_kms_crypto_key_iam_member" "gke_encryption" {
  count = var.security_level == "maximum" ? 1 : 0

  crypto_key_id = google_kms_crypto_key.gke_encryption[0].id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@container-engine-robot.iam.gserviceaccount.com"
}