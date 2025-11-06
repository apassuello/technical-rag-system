# GCP GKE Module for Epic 8 Cloud-Native Multi-Model RAG Platform

## Overview

This Terraform module creates a production-ready Google Kubernetes Engine (GKE) cluster optimized for the Epic 8 Cloud-Native Multi-Model RAG Platform. The module follows Swiss engineering standards emphasizing precision, reliability, security, and efficiency with special focus on Zurich region deployment.

## Architecture

The module provisions:
- **GKE Cluster**: Kubernetes 1.28+ with regional deployment and comprehensive monitoring
- **VPC Network**: Secure network architecture with private nodes and Cloud NAT
- **Node Pools**: Mixed machine types with preemptible instances for cost optimization
- **Security**: Workload Identity, Binary Authorization, Shielded GKE nodes, and Cloud Armor
- **Add-ons**: HPA, VPA, Network Policy (Calico), DNS Cache, and optional Istio
- **Monitoring**: Cloud Monitoring and Logging with Managed Prometheus integration

## Swiss Engineering Standards

### Precision
- Exact resource allocation with environment-specific scaling
- Fine-tuned autoscaling parameters for >70% resource utilization
- Comprehensive labeling and resource organization following GCP best practices

### Reliability
- Regional cluster deployment across multiple zones for 99.9% uptime capability
- Automatic node repair and upgrade with blue-green deployments for production
- Comprehensive health checks and monitoring with Cloud Operations Suite

### Security
- Three security levels: basic, enhanced, maximum
- Workload Identity for secure GCP service authentication
- Shielded GKE nodes with Secure Boot and Integrity Monitoring
- Network policies with Calico for micro-segmentation
- Private cluster configuration with authorized networks

### Efficiency
- Cost optimization with preemptible instances (configurable percentage)
- Right-sizing based on environment (dev/staging/prod)
- Regional persistent disks for production workloads
- Spot instances support for maximum cost savings

## Usage

### Basic Usage

```hcl
module "epic8_gke" {
  source = "./modules/gcp-gke"

  project_id   = "epic8-rag-platform"
  project_name = "epic8-rag"
  environment  = "prod"
  region       = "europe-west6"  # Zurich, Switzerland

  # Swiss compliance
  swiss_compliance_enabled   = true
  data_residency_enforcement = true
  security_level            = "enhanced"

  # Cost optimization
  enable_preemptible_nodes  = true
  preemptible_percentage    = 40
  enable_spot_nodes         = false

  # Epic 8 platform deployment
  deploy_epic8_platform    = true
  epic8_helm_chart_version = "1.0.0"
  epic8_values_file       = "../../helm/epic8-platform/values-gcp-prod.yaml"

  # Additional labels
  additional_labels = {
    team        = "platform-engineering"
    cost_center = "engineering"
    environment = "production"
  }
}
```

### Advanced Configuration

```hcl
module "epic8_gke" {
  source = "./modules/gcp-gke"

  project_id   = "epic8-rag-platform-prod"
  project_name = "epic8-rag"
  environment  = "prod"
  region       = "europe-west6"

  # Network configuration
  network_name   = ""  # Creates new VPC
  subnet_name    = ""  # Creates new subnet
  network_cidr   = "10.0.0.0/16"
  subnet_cidr    = "10.0.0.0/24"
  pods_cidr      = "10.1.0.0/16"
  services_cidr  = "10.2.0.0/16"

  # Security configuration
  security_level          = "maximum"
  enable_private_nodes    = true
  enable_private_endpoint = false
  master_authorized_networks = [
    {
      cidr_block   = "203.0.113.0/24"
      display_name = "Office Network"
    },
    {
      cidr_block   = "198.51.100.0/24"
      display_name = "VPN Network"
    }
  ]

  # Advanced security features
  enable_workload_identity     = true
  enable_binary_authorization  = true
  enable_network_policy       = true

  # Custom node pools
  node_pools = {
    general = {
      machine_type    = "n1-standard-4"
      min_count       = 3
      max_count       = 10
      initial_count   = 6
      disk_size_gb    = 100
      disk_type       = "pd-ssd"
      preemptible     = false
      spot            = false
      auto_repair     = true
      auto_upgrade    = true
      max_surge       = 1
      max_unavailable = 0
      node_labels = {
        "epic8.io/node-type" = "general"
        "epic8.io/workload"  = "api-services"
      }
      node_taints = []
      oauth_scopes = [
        "https://www.googleapis.com/auth/cloud-platform"
      ]
    }

    ml_workloads = {
      machine_type    = "n1-highmem-8"
      min_count       = 1
      max_count       = 6
      initial_count   = 2
      disk_size_gb    = 200
      disk_type       = "pd-ssd"
      preemptible     = false
      spot            = false
      auto_repair     = true
      auto_upgrade    = true
      max_surge       = 1
      max_unavailable = 0
      node_labels = {
        "epic8.io/node-type"    = "ml-workloads"
        "epic8.io/high-memory"  = "true"
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
  }

  # Monitoring and logging
  enable_logging      = true
  logging_components  = ["SYSTEM_COMPONENTS", "WORKLOADS", "API_SERVER"]
  enable_monitoring   = true
  monitoring_components = ["SYSTEM_COMPONENTS", "WORKLOADS", "HPA", "POD"]

  # Maintenance window (Swiss business hours)
  maintenance_window_start_time = "2023-01-01T02:00:00Z"
  maintenance_window_end_time   = "2023-01-01T06:00:00Z"
  maintenance_window_recurrence = "FREQ=WEEKLY;BYDAY=SA"

  additional_labels = {
    team        = "platform-engineering"
    cost_center = "engineering"
    project     = "epic8-rag-platform"
    compliance  = "swiss-gdpr"
  }
}
```

### Multi-Environment Setup

```hcl
# Development Environment
module "epic8_gke_dev" {
  source = "./modules/gcp-gke"

  project_id   = "epic8-rag-dev"
  environment  = "dev"
  region       = "europe-west6"

  security_level           = "basic"
  enable_preemptible_nodes = true
  preemptible_percentage   = 80
  enable_spot_nodes        = true

  # Minimal node pools for cost optimization
  node_pools = {
    general = {
      machine_type  = "e2-medium"
      min_count     = 1
      max_count     = 3
      initial_count = 2
      preemptible   = true
      spot          = true
      # ... other configuration
    }
  }
}

# Production Environment
module "epic8_gke_prod" {
  source = "./modules/gcp-gke"

  project_id   = "epic8-rag-prod"
  environment  = "prod"
  region       = "europe-west6"

  security_level           = "maximum"
  enable_preemptible_nodes = true
  preemptible_percentage   = 40
  enable_spot_nodes        = false

  # Production-grade configuration
  enable_workload_identity    = true
  enable_binary_authorization = true
  enable_network_policy      = true
  enable_backup              = true
  backup_retention_days      = 90

  # ... production node pools and configuration
}
```

## Swiss Region Preferences

The module is optimized for Swiss/EU deployments:

1. **Primary Region**: `europe-west6` (Zurich) - Located in Switzerland
2. **Secondary Region**: `europe-west1` (Belgium) - EU GDPR compliant
3. **Tertiary Region**: `europe-west3` (Frankfurt) - Close to Switzerland
4. **GDPR Compliance**: Automatic data residency enforcement
5. **Swiss Data Protection**: Enhanced security configurations

## Cost Optimization Features

### Preemptible Instances
- Configurable preemptible instance percentage (0-100%)
- Intelligent machine type selection based on environment
- Environment-specific preemptible usage:
  - **Development**: 80% preemptible instances
  - **Staging**: 60% preemptible instances
  - **Production**: 40% preemptible instances

### Spot Instances
- Support for Spot VMs for maximum cost savings
- Automatic fallback to preemptible instances
- Suitable for fault-tolerant workloads

### Right-Sizing
- Environment-specific resource allocation
- Automatic scaling based on workload patterns
- Regional persistent disks for production durability

### Network Optimization
- Cloud NAT for private node internet access
- VPC-native networking for better performance
- Efficient IP address allocation

## Security Features

### Three Security Levels

#### Basic Security
- Standard GKE security features
- Public cluster endpoint with authorized networks
- Basic disk encryption

#### Enhanced Security (Default)
- Workload Identity enabled
- Shielded GKE nodes with Secure Boot
- Network policies with Calico
- Private nodes with Cloud NAT
- Managed Prometheus for monitoring

#### Maximum Security
- Customer-managed KMS keys for encryption
- Binary Authorization for container security
- Private cluster endpoint
- Geographic access restrictions via Cloud Armor
- Comprehensive audit logging

### Compliance Features
- GDPR compliance configurations
- Swiss data residency enforcement
- Comprehensive audit logging
- Resource labeling for compliance tracking
- Cloud Security Command Center integration

## Monitoring and Observability

### Cloud Operations Suite Integration
- Cloud Monitoring for metrics collection
- Cloud Logging for centralized log management
- Managed Prometheus for application metrics
- Cloud Trace for distributed tracing

### Epic 8 Specific Monitoring
- Service-level metrics collection
- Performance monitoring for ML workloads
- Cost tracking with detailed labeling
- Health checks for all Epic 8 services
- Custom dashboards in Cloud Monitoring

## Epic 8 Platform Integration

### Automatic Deployment
The module can automatically deploy the Epic 8 platform using Helm:

```hcl
deploy_epic8_platform    = true
epic8_helm_chart_version = "1.0.0"
epic8_values_file       = "path/to/gcp-values.yaml"
```

### GKE-Specific Configurations
- **Workload Identity**: Secure authentication to GCP services
- **Cloud Armor**: Web Application Firewall protection
- **Global Load Balancer**: Multi-region traffic distribution
- **Managed SSL Certificates**: Automatic certificate provisioning
- **Cloud CDN**: Content delivery network for static assets

### Service Configuration
- **API Gateway**: Auto-scaling with ingress controller
- **Query Analyzer**: Optimized for high-memory instances with ML workloads
- **Retriever Service**: Persistent storage with regional SSD disks
- **Generator Service**: Multi-model support with GPU acceleration (prod)
- **Cache Service**: Redis cluster with high availability
- **Analytics Service**: Managed Prometheus and Grafana integration

## Prerequisites

### GCP Requirements
- GCP project with billing enabled
- Required APIs enabled:
  - Kubernetes Engine API
  - Compute Engine API
  - Cloud Resource Manager API
  - Cloud KMS API (for maximum security)
  - Binary Authorization API (if enabled)
- Service account with appropriate permissions
- Terraform >= 1.5.0
- kubectl and gcloud CLI tools

### Required GCP Permissions
```yaml
roles:
  - roles/container.admin
  - roles/compute.admin
  - roles/iam.serviceAccountAdmin
  - roles/resourcemanager.projectIamAdmin
  - roles/logging.admin
  - roles/monitoring.admin
  - roles/cloudkms.admin  # For maximum security
  - roles/binaryauthorization.attestorsAdmin  # If Binary Authorization is enabled
```

### Swiss Compliance Prerequisites
- Ensure your GCP project is configured for EU data residency
- Configure appropriate data classification and handling procedures
- Implement organization-specific compliance monitoring
- Review GCP compliance certifications for Swiss requirements

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project_id | GCP Project ID | `string` | n/a | yes |
| project_name | Epic 8 project name | `string` | `"epic8-rag"` | no |
| environment | Environment (dev/staging/prod) | `string` | n/a | yes |
| region | GCP region | `string` | `"europe-west6"` | no |
| swiss_compliance_enabled | Enable Swiss/GDPR compliance | `bool` | `true` | no |
| security_level | Security level (basic/enhanced/maximum) | `string` | `"enhanced"` | no |
| enable_preemptible_nodes | Enable preemptible instances | `bool` | `true` | no |
| preemptible_percentage | Percentage of preemptible instances | `number` | `50` | no |
| deploy_epic8_platform | Deploy Epic 8 platform | `bool` | `false` | no |

## Outputs

| Name | Description |
|------|-------------|
| cluster_name | GKE cluster name |
| cluster_endpoint | GKE cluster endpoint |
| cluster_ca_certificate | Cluster CA certificate |
| network_name | VPC network name |
| kubeconfig_command | Command to get kubeconfig |
| swiss_compliance_status | Swiss compliance status |
| cost_optimization | Cost optimization configuration |

## Examples

See the `examples/` directory for complete deployment scenarios:
- `multi-cloud-deployment/` - Multi-cloud Epic 8 deployment
- `swiss-compliant-setup/` - Maximum Swiss compliance configuration
- `cost-optimized-deployment/` - Development environment with cost optimization

## Roadmap

### Planned Features
- Integration with GKE Autopilot for hands-off cluster management
- Support for ARM-based node pools (Tau T2A instances)
- Advanced auto-scaling with custom metrics from Epic 8 services
- Integration with Cloud Run for serverless workloads

### Swiss Market Enhancements
- Integration with Swiss identity providers (Swiss-Sign, SuisseID)
- Support for Swiss financial services compliance frameworks
- Enhanced data sovereignty features
- Integration with Swiss cloud providers

## Support

For issues related to this module:
1. Check the [troubleshooting guide](./docs/troubleshooting.md)
2. Review the [FAQ](./docs/faq.md)
3. Consult GKE documentation for cluster-specific issues
4. Open an issue with detailed logs and configuration

## License

This module is licensed under the MIT License. See [LICENSE](./LICENSE) for full details.