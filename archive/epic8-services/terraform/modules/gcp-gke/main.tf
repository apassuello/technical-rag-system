# GCP GKE Module for Epic 8 Cloud-Native Multi-Model RAG Platform
# Swiss Engineering Standards: Precision, Reliability, Security, Efficiency
# Author: Claude (Terraform Specialist)
# Version: 1.0.0

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.84"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.84"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
}

# Local values for Swiss engineering precision
locals {
  # Swiss region preferences with fallback
  swiss_regions = {
    primary   = "europe-west6"   # Zurich (Switzerland)
    secondary = "europe-west1"   # Belgium (EU GDPR compliant)
    tertiary  = "europe-west3"   # Frankfurt (close to Switzerland)
  }

  # Environment-specific resource sizing following Swiss efficiency standards
  environment_configs = {
    dev = {
      min_nodes         = 1
      max_nodes         = 3
      initial_nodes     = 2
      machine_types     = ["e2-medium", "e2-standard-2"]
      preemptible_ratio = 0.8  # Cost optimization
      disk_size         = 50
      enable_autoscaling = true
    }
    staging = {
      min_nodes         = 2
      max_nodes         = 6
      initial_nodes     = 3
      machine_types     = ["n1-standard-2", "n1-standard-4"]
      preemptible_ratio = 0.6
      disk_size         = 100
      enable_autoscaling = true
    }
    prod = {
      min_nodes         = 3
      max_nodes         = 12
      initial_nodes     = 6
      machine_types     = ["n1-standard-4", "n1-standard-8"]
      preemptible_ratio = 0.4  # Higher reliability for production
      disk_size         = 200
      enable_autoscaling = true
    }
  }

  # Swiss compliance and security labels
  common_labels = merge(var.additional_labels, {
    project             = "epic8-rag-platform"
    environment         = var.environment
    managed_by          = "terraform"
    swiss_compliance    = var.swiss_compliance_enabled ? "enabled" : "disabled"
    data_residency      = "eu"
    cost_center         = var.cost_center
    owner               = var.owner
    security_level      = var.security_level
    backup_required     = "true"
    monitoring_enabled  = "true"
  })

  # GKE cluster name with Swiss naming convention
  cluster_name = "${var.project_name}-${var.environment}-gke-${random_id.cluster_suffix.hex}"

  # Current environment configuration
  current_config = local.environment_configs[var.environment]
}

# Random ID for unique cluster naming
resource "random_id" "cluster_suffix" {
  byte_length = 4
}

# Data source for available zones in the region
data "google_compute_zones" "available" {
  region = var.region
  status = "UP"
}

# Data source for latest GKE version
data "google_container_engine_versions" "gke_version" {
  location       = var.region
  version_prefix = var.kubernetes_version
}

# Data source for current project
data "google_client_config" "default" {}

# Data source for project information
data "google_project" "project" {
  project_id = var.project_id
}