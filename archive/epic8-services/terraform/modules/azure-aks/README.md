# Azure AKS Module for Epic 8 Cloud-Native Multi-Model RAG Platform

## Overview

This Terraform module creates a production-ready Azure Kubernetes Service (AKS) cluster optimized for the Epic 8 Cloud-Native Multi-Model RAG Platform. The module follows Swiss engineering standards emphasizing precision, reliability, security, and efficiency with special focus on Switzerland North region deployment.

## Architecture

The module provisions:
- **AKS Cluster**: Kubernetes 1.28+ with regional deployment and comprehensive monitoring
- **Virtual Network**: Secure network architecture with subnets, NSGs, and NAT Gateway
- **Node Pools**: Mixed VM sizes with spot instances for cost optimization
- **Security**: Azure AD integration, RBAC, Workload Identity, and Azure Policy
- **Add-ons**: HPA, VPA, KEDA, Network Policy, and Azure Key Vault Secrets Provider
- **Monitoring**: Azure Monitor, Log Analytics, and Microsoft Defender for Containers

## Swiss Engineering Standards

### Precision
- Exact resource allocation with environment-specific scaling
- Fine-tuned autoscaling parameters for >70% resource utilization
- Comprehensive tagging and resource organization following Azure best practices

### Reliability
- Multi-zone deployment across availability zones for 99.9% uptime capability
- Automatic node repair and upgrade with surge upgrade strategy
- Comprehensive health monitoring with Azure Monitor and Log Analytics

### Security
- Three security levels: basic, enhanced, maximum
- Azure AD integration with RBAC for fine-grained access control
- Workload Identity for secure Azure service authentication
- Network security groups and network policies for micro-segmentation
- Customer-managed encryption keys for maximum security

### Efficiency
- Cost optimization with spot instances (configurable percentage)
- Right-sizing based on environment (dev/staging/prod)
- Standard and Premium storage options based on workload requirements
- NAT Gateway for efficient outbound connectivity

## Usage

### Basic Usage

```hcl
module "epic8_aks" {
  source = "./modules/azure-aks"

  project_name = "epic8-rag"
  environment  = "prod"
  location     = "Switzerland North"

  # Swiss compliance
  swiss_compliance_enabled   = true
  data_residency_enforcement = true
  security_level            = "enhanced"

  # Cost optimization
  enable_spot_instances = true
  spot_percentage      = 40
  spot_max_price       = -1  # Use current on-demand price

  # Epic 8 platform deployment
  deploy_epic8_platform    = true
  epic8_helm_chart_version = "1.0.0"
  epic8_values_file       = "../../helm/epic8-platform/values-azure-prod.yaml"

  # Additional tags
  additional_tags = {
    team        = "platform-engineering"
    cost_center = "engineering"
    environment = "production"
  }
}
```

### Advanced Configuration

```hcl
module "epic8_aks" {
  source = "./modules/azure-aks"

  project_name        = "epic8-rag"
  environment         = "prod"
  location            = "Switzerland North"
  resource_group_name = "epic8-prod-rg"

  # Network configuration
  vnet_name               = ""  # Creates new VNet
  subnet_name             = ""  # Creates new subnet
  vnet_address_space      = ["10.0.0.0/16"]
  subnet_address_prefix   = "10.0.1.0/24"
  pod_subnet_address_prefix = "10.0.2.0/24"
  service_cidr           = "10.1.0.0/16"
  dns_service_ip         = "10.1.0.10"

  # Security configuration
  security_level         = "maximum"
  enable_private_cluster = false
  enable_azure_rbac     = true
  azure_rbac_admin_group_object_ids = [
    "12345678-1234-1234-1234-123456789012"  # Platform Admin Group
  ]

  # Advanced security features
  enable_workload_identity              = true
  enable_azure_policy                  = true
  enable_azure_keyvault_secrets_provider = true
  enable_defender                      = true
  enable_host_encryption              = true
  enable_disk_encryption              = true

  # Default node pool configuration
  default_node_pool = {
    name                = "system"
    vm_size             = "Standard_D4s_v3"
    node_count          = 3
    min_count          = 3
    max_count          = 10
    enable_auto_scaling = true
    availability_zones  = ["1", "2", "3"]
    max_pods           = 30
    os_disk_size_gb    = 128
    os_disk_type       = "Managed"
    enable_node_public_ip = false
    node_labels = {
      "epic8.io/node-type" = "system"
      "epic8.io/workload"  = "system"
    }
    node_taints = ["CriticalAddonsOnly=true:NoSchedule"]
  }

  # Additional node pools for different workloads
  additional_node_pools = {
    general = {
      vm_size             = "Standard_D4s_v3"
      node_count          = 3
      min_count          = 2
      max_count          = 10
      enable_auto_scaling = true
      availability_zones  = ["1", "2", "3"]
      max_pods           = 30
      os_disk_size_gb    = 128
      os_disk_type       = "Managed"
      enable_node_public_ip = false
      spot_max_price     = -1
      priority           = "Regular"
      eviction_policy    = "Delete"
      node_labels = {
        "epic8.io/node-type" = "general"
        "epic8.io/workload"  = "api-services"
      }
      node_taints = []
    }

    ml_workloads = {
      vm_size             = "Standard_D8s_v3"
      node_count          = 2
      min_count          = 1
      max_count          = 6
      enable_auto_scaling = true
      availability_zones  = ["1", "2", "3"]
      max_pods           = 20
      os_disk_size_gb    = 256
      os_disk_type       = "Managed"
      enable_node_public_ip = false
      spot_max_price     = -1
      priority           = "Regular"
      eviction_policy    = "Delete"
      node_labels = {
        "epic8.io/node-type"    = "ml-workloads"
        "epic8.io/high-memory"  = "true"
        "epic8.io/ml-workload"  = "true"
      }
      node_taints = ["epic8.io/ml-workload=true:NoSchedule"]
    }

    spot_workloads = {
      vm_size             = "Standard_D4s_v3"
      node_count          = 0
      min_count          = 0
      max_count          = 10
      enable_auto_scaling = true
      availability_zones  = ["1", "2", "3"]
      max_pods           = 30
      os_disk_size_gb    = 128
      os_disk_type       = "Managed"
      enable_node_public_ip = false
      spot_max_price     = 0.05  # Maximum $0.05/hour
      priority           = "Spot"
      eviction_policy    = "Delete"
      node_labels = {
        "epic8.io/node-type"     = "spot"
        "epic8.io/cost-optimized" = "true"
        "kubernetes.azure.com/scalesetpriority" = "spot"
      }
      node_taints = ["kubernetes.azure.com/scalesetpriority=spot:NoSchedule"]
    }
  }

  # Add-ons configuration
  enable_oms_agent                       = true
  enable_azure_policy                   = true
  enable_vertical_pod_autoscaler        = true
  enable_workload_identity              = true
  enable_image_cleaner                  = true
  enable_azure_keyvault_secrets_provider = true

  # Network configuration
  enable_azure_cni  = true
  network_plugin    = "azure"
  network_policy    = "azure"

  # Monitoring
  log_analytics_workspace_id = ""  # Creates new workspace

  # Maintenance window (Swiss business hours)
  maintenance_window = {
    allowed = [{
      day   = "Saturday"
      hours = [2, 3, 4, 5]
    }]
    not_allowed = [{
      start = "2023-12-24T00:00:00Z"
      end   = "2023-12-26T23:59:59Z"
    }]
  }

  additional_tags = {
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
module "epic8_aks_dev" {
  source = "./modules/azure-aks"

  project_name = "epic8-rag"
  environment  = "dev"
  location     = "Switzerland North"

  security_level      = "basic"
  enable_spot_instances = true
  spot_percentage     = 80

  # Minimal configuration for cost optimization
  default_node_pool = {
    vm_size         = "Standard_B2s"
    min_count      = 1
    max_count      = 3
    # ... other configuration
  }

  additional_node_pools = {}  # No additional pools for dev
}

# Production Environment
module "epic8_aks_prod" {
  source = "./modules/azure-aks"

  project_name = "epic8-rag"
  environment  = "prod"
  location     = "Switzerland North"

  security_level      = "maximum"
  enable_spot_instances = true
  spot_percentage     = 40

  # Production-grade configuration
  enable_workload_identity              = true
  enable_azure_policy                  = true
  enable_defender                      = true
  enable_azure_keyvault_secrets_provider = true

  # ... production node pools and configuration
}
```

## Swiss Region Preferences

The module is optimized for Swiss/EU deployments:

1. **Primary Region**: `Switzerland North` - Located in Switzerland
2. **Secondary Region**: `Switzerland West` - Swiss backup region
3. **Tertiary Region**: `West Europe` - EU GDPR compliant (Amsterdam)
4. **GDPR Compliance**: Automatic data residency enforcement
5. **Swiss Data Protection**: Enhanced security configurations

## Cost Optimization Features

### Spot Instances
- Configurable spot instance percentage (0-100%)
- Flexible pricing with maximum price limits
- Environment-specific spot usage:
  - **Development**: 80% spot instances
  - **Staging**: 60% spot instances
  - **Production**: 40% spot instances

### Right-Sizing
- Environment-specific VM size selection
- Automatic scaling based on workload patterns
- Different storage tiers (Standard SSD, Premium SSD)

### Network Optimization
- NAT Gateway for efficient outbound connectivity
- Azure CNI for optimized pod networking
- Service endpoints for cost-effective Azure service access

## Security Features

### Three Security Levels

#### Basic Security
- Standard AKS security features
- Azure AD integration
- Basic network security groups
- Managed identity for cluster

#### Enhanced Security (Default)
- Azure RBAC for Kubernetes authorization
- Workload Identity for pod-to-Azure authentication
- Network policies with Azure CNI
- Azure Policy add-on for governance
- Microsoft Defender for Containers

#### Maximum Security
- Customer-managed encryption keys (CMEK)
- Private cluster endpoint
- Host encryption for nodes
- Azure Key Vault Secrets Provider
- Network security groups with restrictive rules
- Private DNS zones

### Compliance Features
- GDPR compliance configurations
- Swiss data residency enforcement
- Comprehensive audit logging via Azure Monitor
- Resource tagging for compliance tracking
- Azure Policy constraints for governance

## Monitoring and Observability

### Azure Monitor Integration
- Log Analytics workspace for centralized logging
- Container Insights for container-specific metrics
- Application Insights integration capabilities
- Custom metrics and dashboards

### Epic 8 Specific Monitoring
- Service-level metrics collection
- Performance monitoring for ML workloads
- Cost tracking with detailed tagging
- Health checks for all Epic 8 services
- Integration with Prometheus and Grafana

## Epic 8 Platform Integration

### Automatic Deployment
The module can automatically deploy the Epic 8 platform using Helm:

```hcl
deploy_epic8_platform    = true
epic8_helm_chart_version = "1.0.0"
epic8_values_file       = "path/to/azure-values.yaml"
```

### AKS-Specific Configurations
- **Workload Identity**: Secure authentication to Azure services
- **Application Gateway**: Ingress controller with WAF capabilities
- **Azure Files**: Shared storage for multi-pod access
- **Azure Disk**: High-performance storage for databases
- **Azure Policy**: Governance and compliance enforcement

### Service Configuration
- **API Gateway**: Auto-scaling with Application Gateway ingress
- **Query Analyzer**: Optimized for high-memory VMs with ML workloads
- **Retriever Service**: Persistent storage with Premium SSD
- **Generator Service**: Multi-model support with high-memory instances
- **Cache Service**: Redis cluster with high availability
- **Analytics Service**: Azure Monitor and custom dashboards

## Prerequisites

### Azure Requirements
- Azure subscription with sufficient quotas
- Required resource providers registered:
  - Microsoft.ContainerService
  - Microsoft.Compute
  - Microsoft.Network
  - Microsoft.Storage
  - Microsoft.KeyVault (for maximum security)
- Service principal or managed identity with appropriate permissions
- Terraform >= 1.5.0
- kubectl and Azure CLI tools

### Required Azure Permissions
```yaml
roles:
  - Azure Kubernetes Service Cluster Admin Role
  - Network Contributor
  - Storage Account Contributor
  - Key Vault Administrator  # For maximum security
  - Security Admin  # For Azure Policy and Defender
```

### Swiss Compliance Prerequisites
- Ensure your Azure subscription is configured for EU data residency
- Configure appropriate data classification and handling procedures
- Implement organization-specific compliance monitoring
- Review Azure compliance certifications for Swiss requirements

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project_name | Epic 8 project name | `string` | `"epic8-rag"` | no |
| environment | Environment (dev/staging/prod) | `string` | n/a | yes |
| location | Azure region | `string` | `"Switzerland North"` | no |
| swiss_compliance_enabled | Enable Swiss/GDPR compliance | `bool` | `true` | no |
| security_level | Security level (basic/enhanced/maximum) | `string` | `"enhanced"` | no |
| enable_spot_instances | Enable spot instances | `bool` | `true` | no |
| spot_percentage | Percentage of spot instances | `number` | `50` | no |
| deploy_epic8_platform | Deploy Epic 8 platform | `bool` | `false` | no |

## Outputs

| Name | Description |
|------|-------------|
| cluster_name | AKS cluster name |
| cluster_endpoint | AKS cluster endpoint |
| cluster_ca_certificate | Cluster CA certificate |
| resource_group_name | Resource group name |
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
- Integration with Azure Container Apps for serverless workloads
- Support for ARM-based node pools (Dpsv5, Epsv5 series)
- Advanced auto-scaling with Azure Monitor custom metrics
- Integration with Azure OpenAI services for Epic 8

### Swiss Market Enhancements
- Integration with Swiss identity providers
- Support for Swiss financial services compliance frameworks
- Enhanced data sovereignty features
- Integration with Swiss cloud providers

## Support

For issues related to this module:
1. Check the [troubleshooting guide](./docs/troubleshooting.md)
2. Review the [FAQ](./docs/faq.md)
3. Consult AKS documentation for cluster-specific issues
4. Open an issue with detailed logs and configuration

## License

This module is licensed under the MIT License. See [LICENSE](./LICENSE) for full details.