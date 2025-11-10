# GCP VPC Configuration for GKE
# Swiss Engineering Standards: Secure, Efficient Network Architecture

# Local values for network configuration
locals {
  create_network = var.network_name == ""
  create_subnet  = var.subnet_name == ""
  network_name   = local.create_network ? "${local.cluster_name}-vpc" : var.network_name
  subnet_name    = local.create_subnet ? "${local.cluster_name}-subnet" : var.subnet_name
}

# Data sources for existing network and subnet (if provided)
data "google_compute_network" "existing" {
  count = local.create_network ? 0 : 1
  name  = var.network_name
}

data "google_compute_subnetwork" "existing" {
  count  = local.create_subnet ? 0 : 1
  name   = var.subnet_name
  region = var.region
}

# VPC Network (created if network_name is empty)
resource "google_compute_network" "vpc" {
  count = local.create_network ? 1 : 0

  name                    = local.network_name
  auto_create_subnetworks = false
  mtu                     = 1460
  routing_mode           = "REGIONAL"

  # Swiss engineering: comprehensive labeling
  labels = merge(local.common_labels, {
    component = "networking"
    purpose   = "gke-cluster"
  })

  # Deletion protection for production environments
  deletion_policy = var.environment == "prod" ? "ABANDON" : null
}

# Subnet (created if subnet_name is empty)
resource "google_compute_subnetwork" "subnet" {
  count = local.create_subnet ? 1 : 0

  name          = local.subnet_name
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = local.create_network ? google_compute_network.vpc[0].id : data.google_compute_network.existing[0].id

  # Secondary IP ranges for pods and services
  secondary_ip_range {
    range_name    = "${local.cluster_name}-pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "${local.cluster_name}-services"
    ip_cidr_range = var.services_cidr
  }

  # Enable private Google access for cost optimization and security
  private_ip_google_access = true

  # Flow logs for security monitoring (enhanced/maximum security levels)
  dynamic "log_config" {
    for_each = var.security_level != "basic" ? [1] : []
    content {
      aggregation_interval = "INTERVAL_5_SEC"
      flow_sampling        = 1.0
      metadata            = "INCLUDE_ALL_METADATA"
      metadata_fields     = []
      filter_expr         = "true"
    }
  }

  # Purpose and role for Epic 8 workloads
  purpose = "PRIVATE"
  role    = null

  # Labels for Swiss compliance and cost tracking
  labels = merge(local.common_labels, {
    component = "networking"
    purpose   = "gke-subnet"
  })
}

# Cloud Router for NAT Gateway
resource "google_compute_router" "router" {
  count = var.enable_private_nodes ? 1 : 0

  name    = "${local.cluster_name}-router"
  region  = var.region
  network = local.create_network ? google_compute_network.vpc[0].id : data.google_compute_network.existing[0].id

  bgp {
    asn = 64514
  }

  # Labels for resource tracking
  labels = merge(local.common_labels, {
    component = "networking"
    purpose   = "nat-gateway"
  })
}

# Cloud NAT for outbound internet access from private nodes
resource "google_compute_router_nat" "nat" {
  count = var.enable_private_nodes ? 1 : 0

  name                               = "${local.cluster_name}-nat"
  router                             = google_compute_router.router[0].name
  region                             = var.region
  nat_ip_allocate_option            = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  # Log configuration for monitoring
  log_config {
    enable = var.security_level != "basic"
    filter = "ERRORS_ONLY"
  }

  # Endpoint configuration for efficiency
  enable_endpoint_independent_mapping = true

  # NAT rules for Epic 8 specific traffic (if needed)
  dynamic "rules" {
    for_each = var.environment == "prod" ? [1] : []
    content {
      rule_number = 100
      description = "Epic 8 ML workloads NAT rule"
      match       = "destination.ip == '0.0.0.0/0'"
      action {
        source_nat_active_ips = []
      }
    }
  }
}

# Firewall rules for GKE cluster
resource "google_compute_firewall" "gke_cluster" {
  count = local.create_network ? 1 : 0

  name    = "${local.cluster_name}-firewall"
  network = google_compute_network.vpc[0].name

  # Allow internal cluster communication
  allow {
    protocol = "tcp"
    ports    = ["443", "80", "8080", "10250"]
  }

  allow {
    protocol = "udp"
    ports    = ["53"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [var.subnet_cidr, var.pods_cidr, var.services_cidr]
  target_tags   = ["gke-node"]

  # Labels for security tracking
  labels = merge(local.common_labels, {
    component = "security"
    purpose   = "gke-cluster"
  })
}

# Firewall rules for Epic 8 services
resource "google_compute_firewall" "epic8_services" {
  count = local.create_network ? 1 : 0

  name    = "${local.cluster_name}-epic8-services"
  network = google_compute_network.vpc[0].name

  # HTTP and HTTPS traffic
  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  # gRPC traffic for service communication
  allow {
    protocol = "tcp"
    ports    = ["8080", "8081", "8082", "8083", "8084", "8085"]
  }

  # Metrics and monitoring
  allow {
    protocol = "tcp"
    ports    = ["9090", "9091", "9092", "9093", "9094", "9095"]
  }

  # Redis cache
  allow {
    protocol = "tcp"
    ports    = ["6379"]
  }

  source_ranges = [var.subnet_cidr]
  target_tags   = ["epic8-service"]

  # Labels for Epic 8 service tracking
  labels = merge(local.common_labels, {
    component = "security"
    purpose   = "epic8-services"
    platform  = "epic8-rag"
  })
}

# Firewall rules for load balancer health checks
resource "google_compute_firewall" "allow_health_check" {
  count = local.create_network && var.enable_http_load_balancing ? 1 : 0

  name    = "${local.cluster_name}-allow-health-check"
  network = google_compute_network.vpc[0].name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8080"]
  }

  # Google Cloud health check source ranges
  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["gke-node", "epic8-service"]

  # Labels for health check tracking
  labels = merge(local.common_labels, {
    component = "security"
    purpose   = "health-checks"
  })
}

# Firewall rules for SSH access (enhanced security level and above)
resource "google_compute_firewall" "allow_ssh" {
  count = local.create_network && var.security_level != "basic" ? 1 : 0

  name    = "${local.cluster_name}-allow-ssh"
  network = google_compute_network.vpc[0].name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  # Restrict SSH access to specific IP ranges for maximum security
  source_ranges = var.security_level == "maximum" && length(var.master_authorized_networks) > 0 ? [
    for network in var.master_authorized_networks : network.cidr_block
  ] : ["0.0.0.0/0"]

  target_tags = ["gke-node"]

  # Labels for SSH access tracking
  labels = merge(local.common_labels, {
    component = "security"
    purpose   = "ssh-access"
  })
}

# Private Service Access for managed services (maximum security)
resource "google_compute_global_address" "private_service_access" {
  count = var.security_level == "maximum" && local.create_network ? 1 : 0

  name          = "${local.cluster_name}-private-service-access"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc[0].id

  labels = merge(local.common_labels, {
    component = "networking"
    purpose   = "private-service-access"
  })
}

resource "google_service_networking_connection" "private_service_access" {
  count = var.security_level == "maximum" && local.create_network ? 1 : 0

  network                 = google_compute_network.vpc[0].id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_access[0].name]

  depends_on = [google_compute_global_address.private_service_access]
}

# VPC Flow Logs export to Cloud Logging (for Swiss compliance)
resource "google_logging_project_sink" "vpc_flow_logs" {
  count = var.swiss_compliance_enabled && var.security_level != "basic" ? 1 : 0

  name        = "${local.cluster_name}-vpc-flow-logs"
  destination = "logging.googleapis.com/projects/${var.project_id}/logs/${local.cluster_name}-vpc-flows"

  filter = <<-EOT
    resource.type="gce_subnetwork" AND
    jsonPayload.src_instance.vm_name!="" AND
    jsonPayload.dest_instance.vm_name!=""
  EOT

  # Ensure logs are retained for compliance
  unique_writer_identity = true

  # Exclusions for cost optimization
  dynamic "exclusions" {
    for_each = var.environment != "prod" ? [1] : []
    content {
      name   = "exclude-health-checks"
      filter = "jsonPayload.src_port=\"8080\" OR jsonPayload.dest_port=\"8080\""
    }
  }
}