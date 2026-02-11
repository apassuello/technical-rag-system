# AWS EKS Module for Epic 8 Cloud-Native Multi-Model RAG Platform
# Swiss Engineering Standards: Precision, Reliability, Security, Efficiency
# Author: Claude (Terraform Specialist)
# Version: 1.0.0

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

# Local values for Swiss engineering precision
locals {
  # Swiss region preferences with fallback
  swiss_regions = {
    primary   = "eu-central-1"    # Frankfurt (closest to Switzerland)
    secondary = "eu-west-1"       # Ireland (EU GDPR compliant)
  }

  # Environment-specific resource sizing following Swiss efficiency standards
  environment_configs = {
    dev = {
      min_nodes     = 1
      max_nodes     = 3
      desired_nodes = 2
      instance_types = ["t3.medium", "t3.large"]
      spot_percentage = 80  # Cost optimization
    }
    staging = {
      min_nodes     = 2
      max_nodes     = 6
      desired_nodes = 3
      instance_types = ["c5.large", "m5.large"]
      spot_percentage = 60
    }
    prod = {
      min_nodes     = 3
      max_nodes     = 12
      desired_nodes = 6
      instance_types = ["c5.xlarge", "m5.xlarge", "r5.xlarge"]
      spot_percentage = 40  # Higher reliability for production
    }
  }

  # Swiss compliance and security tags
  common_tags = merge(var.additional_tags, {
    Project             = "Epic8-RAG-Platform"
    Environment         = var.environment
    ManagedBy          = "Terraform"
    SwissCompliance    = "GDPR"
    DataResidency      = "EU"
    CostCenter         = var.cost_center
    Owner              = var.owner
    SecurityLevel      = var.security_level
    BackupRequired     = "true"
    MonitoringEnabled  = "true"
  })

  # EKS cluster name with Swiss naming convention
  cluster_name = "${var.project_name}-${var.environment}-eks-${random_id.cluster_suffix.hex}"
}

# Random ID for unique cluster naming
resource "random_id" "cluster_suffix" {
  byte_length = 4
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# Data source for EKS service account
data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}