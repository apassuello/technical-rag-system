# Multi-Cloud Epic 8 RAG Platform Deployment
# Swiss Engineering Standards: Production-Ready Multi-Cloud Infrastructure

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.84"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
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

  backend "s3" {
    bucket = "epic8-terraform-state"
    key    = "multi-cloud/terraform.tfstate"
    region = "eu-central-1"

    dynamodb_table = "epic8-terraform-locks"
    encrypt        = true
  }
}

# Local values for multi-cloud configuration
locals {
  # Common configuration
  common_config = {
    project_name            = "epic8-rag"
    environment            = "prod"
    swiss_compliance_enabled = true
    security_level         = "enhanced"

    # Epic 8 platform configuration
    deploy_epic8_platform    = true
    epic8_helm_chart_version = "1.0.0"

    # Cost optimization
    enable_spot_instances = true
    spot_percentage      = 40

    # Monitoring and observability
    enable_monitoring = true
    enable_tracing   = true

    # Common tags/labels
    common_tags = {
      Project             = "Epic8-RAG-Platform"
      Environment         = "production"
      ManagedBy          = "Terraform"
      SwissCompliance    = "enabled"
      CostCenter         = "engineering"
      Owner              = "platform-team"
      DeploymentStrategy = "multi-cloud"
    }
  }
}

# AWS EKS Deployment (Primary - Frankfurt)
module "aws_eks_primary" {
  source = "../../modules/aws-eks"

  # Core configuration
  project_name = local.common_config.project_name
  environment  = local.common_config.environment
  region       = "eu-central-1"  # Frankfurt

  # Swiss compliance
  swiss_compliance_enabled   = local.common_config.swiss_compliance_enabled
  data_residency_enforcement = true
  security_level            = local.common_config.security_level

  # Network configuration
  vpc_cidr             = "10.1.0.0/16"
  private_subnet_cidrs = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
  public_subnet_cidrs  = ["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]

  # Kubernetes configuration
  kubernetes_version = "1.28"

  # Cost optimization
  enable_spot_instances     = local.common_config.enable_spot_instances
  spot_instance_percentage  = local.common_config.spot_percentage
  single_nat_gateway       = false  # High availability for production

  # Add-ons
  enable_aws_load_balancer_controller = true
  enable_cluster_autoscaler          = true
  enable_metrics_server              = true
  enable_ebs_csi_driver             = true

  # Epic 8 platform
  deploy_epic8_platform    = local.common_config.deploy_epic8_platform
  epic8_helm_chart_version = local.common_config.epic8_helm_chart_version
  epic8_values_file       = "${path.module}/values/aws-prod.yaml"

  # Monitoring
  enable_cluster_logging = local.common_config.enable_monitoring
  log_retention_days     = 90

  additional_tags = local.common_config.common_tags

  providers = {
    aws = aws.frankfurt
  }
}

# GCP GKE Deployment (Secondary - Zurich)
module "gcp_gke_secondary" {
  source = "../../modules/gcp-gke"

  # Core configuration
  project_id   = "epic8-rag-platform-prod"
  project_name = local.common_config.project_name
  environment  = local.common_config.environment
  region       = "europe-west6"  # Zurich

  # Swiss compliance
  swiss_compliance_enabled   = local.common_config.swiss_compliance_enabled
  data_residency_enforcement = true
  security_level            = local.common_config.security_level

  # Network configuration
  network_cidr   = "10.2.0.0/16"
  subnet_cidr    = "10.2.1.0/24"
  pods_cidr      = "10.2.16.0/20"
  services_cidr  = "10.2.32.0/20"

  # Kubernetes configuration
  kubernetes_version = "1.28"
  release_channel   = "STABLE"

  # Cost optimization
  enable_preemptible_nodes = local.common_config.enable_spot_instances
  preemptible_percentage   = local.common_config.spot_percentage

  # Security
  enable_workload_identity     = true
  enable_binary_authorization  = true
  enable_network_policy       = true
  enable_private_nodes        = true

  # Add-ons
  enable_http_load_balancing          = true
  enable_horizontal_pod_autoscaling   = true
  enable_vertical_pod_autoscaling     = true

  # Epic 8 platform
  deploy_epic8_platform    = local.common_config.deploy_epic8_platform
  epic8_helm_chart_version = local.common_config.epic8_helm_chart_version
  epic8_values_file       = "${path.module}/values/gcp-prod.yaml"

  # Monitoring
  enable_logging     = local.common_config.enable_monitoring
  enable_monitoring  = local.common_config.enable_monitoring
  logging_components = ["SYSTEM_COMPONENTS", "WORKLOADS", "API_SERVER"]

  additional_labels = local.common_config.common_tags

  providers = {
    google = google.zurich
  }
}

# Azure AKS Deployment (Tertiary - Switzerland North)
module "azure_aks_tertiary" {
  source = "../../modules/azure-aks"

  # Core configuration
  project_name = local.common_config.project_name
  environment  = local.common_config.environment
  location     = "Switzerland North"

  # Swiss compliance
  swiss_compliance_enabled   = local.common_config.swiss_compliance_enabled
  data_residency_enforcement = true
  security_level            = local.common_config.security_level

  # Network configuration
  vnet_address_space      = ["10.3.0.0/16"]
  subnet_address_prefix   = "10.3.1.0/24"
  pod_subnet_address_prefix = "10.3.2.0/24"
  service_cidr           = "10.3.32.0/20"
  dns_service_ip         = "10.3.32.10"

  # Kubernetes configuration
  kubernetes_version        = "1.28"
  automatic_channel_upgrade = "stable"

  # Cost optimization
  enable_spot_instances = local.common_config.enable_spot_instances
  spot_percentage      = local.common_config.spot_percentage

  # Security
  enable_workload_identity              = true
  enable_azure_policy                  = true
  enable_azure_keyvault_secrets_provider = true
  enable_defender                      = true

  # Add-ons
  enable_oms_agent                    = true
  enable_vertical_pod_autoscaler     = true
  enable_image_cleaner               = true

  # Epic 8 platform
  deploy_epic8_platform    = local.common_config.deploy_epic8_platform
  epic8_helm_chart_version = local.common_config.epic8_helm_chart_version
  epic8_values_file       = "${path.module}/values/azure-prod.yaml"

  additional_tags = local.common_config.common_tags

  providers = {
    azurerm = azurerm.switzerland
  }
}

# Shared Monitoring Stack (Deployed on AWS primary)
module "monitoring" {
  source = "../../modules/shared/monitoring"

  # Core configuration
  environment                = local.common_config.environment
  cluster_name              = module.aws_eks_primary.cluster_name
  monitoring_namespace      = "monitoring"
  swiss_compliance_enabled  = local.common_config.swiss_compliance_enabled

  # Component toggles
  enable_prometheus     = true
  enable_grafana       = true
  enable_alertmanager  = true
  enable_jaeger        = local.common_config.enable_tracing
  enable_opentelemetry = local.common_config.enable_tracing

  # Storage
  storage_class = "epic8-fast"

  # Ingress
  enable_ingress = true
  domain_name   = "epic8.yourdomain.com"
  enable_tls    = true

  # Authentication
  grafana_admin_password = var.grafana_admin_password
  enable_oauth          = true
  oauth_client_id       = var.oauth_client_id
  oauth_client_secret   = var.oauth_client_secret

  # Alerting
  alert_webhook_url = var.slack_webhook_url
  alert_email_to   = var.alert_email

  depends_on = [module.aws_eks_primary]

  providers = {
    kubernetes = kubernetes.aws
    helm      = helm.aws
  }
}

# Shared Security Stack (Deployed across all clusters)
module "security_aws" {
  source = "../../modules/shared/security"

  # Core configuration
  environment              = local.common_config.environment
  swiss_compliance_enabled = local.common_config.swiss_compliance_enabled
  security_level          = local.common_config.security_level

  # Security features
  enable_pod_security_standards = true
  enable_network_policies       = true
  enable_rbac                  = true
  enable_sealed_secrets        = true
  enable_falco                 = true

  # Epic 8 secrets
  epic8_secrets = {
    epic8-api-keys = {
      openai_api_key    = var.openai_api_key
      anthropic_api_key = var.anthropic_api_key
      mistral_api_key   = var.mistral_api_key
    }
  }

  depends_on = [module.aws_eks_primary]

  providers = {
    kubernetes = kubernetes.aws
    helm      = helm.aws
  }
}

# Global DNS and Traffic Management
resource "aws_route53_zone" "epic8" {
  name = "epic8.yourdomain.com"

  tags = local.common_config.common_tags

  provider = aws.frankfurt
}

# Health checks for multi-cloud failover
resource "aws_route53_health_check" "aws_primary" {
  fqdn                            = "epic8-aws.yourdomain.com"
  port                            = 443
  type                            = "HTTPS"
  resource_path                   = "/health"
  failure_threshold               = "3"
  request_interval                = "30"
  cloudwatch_logs_region          = "eu-central-1"
  cloudwatch_alarm_region         = "eu-central-1"
  insufficient_data_health_status = "Failure"

  tags = merge(local.common_config.common_tags, {
    Name = "Epic8-AWS-Health-Check"
  })

  provider = aws.frankfurt
}

# Weighted routing for traffic distribution
resource "aws_route53_record" "epic8_weighted" {
  for_each = {
    aws = {
      cluster_endpoint = module.aws_eks_primary.cluster_endpoint
      weight          = 70  # Primary traffic
      health_check_id = aws_route53_health_check.aws_primary.id
    }
    gcp = {
      cluster_endpoint = module.gcp_gke_secondary.cluster_endpoint
      weight          = 20  # Secondary traffic
      health_check_id = null
    }
    azure = {
      cluster_endpoint = module.azure_aks_tertiary.cluster_endpoint
      weight          = 10  # Tertiary traffic
      health_check_id = null
    }
  }

  zone_id = aws_route53_zone.epic8.zone_id
  name    = "api.epic8.yourdomain.com"
  type    = "CNAME"
  ttl     = 60

  weighted_routing_policy {
    weight = each.value.weight
  }

  set_identifier  = each.key
  records        = [each.value.cluster_endpoint]
  health_check_id = each.value.health_check_id

  provider = aws.frankfurt
}

# Cost tracking and optimization
resource "aws_budgets_budget" "epic8_cost_budget" {
  name         = "epic8-monthly-budget"
  budget_type  = "COST"
  limit_amount = "1000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  time_period_start = "2024-01-01_00:00"

  cost_filters {
    tag {
      key    = "Project"
      values = ["Epic8-RAG-Platform"]
    }
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = [var.cost_alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.cost_alert_email]
  }

  tags = local.common_config.common_tags

  provider = aws.frankfurt
}