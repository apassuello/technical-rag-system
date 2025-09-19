# AWS EKS Module for Epic 8 Cloud-Native Multi-Model RAG Platform

## Overview

This Terraform module creates a production-ready Amazon EKS cluster optimized for the Epic 8 Cloud-Native Multi-Model RAG Platform. The module follows Swiss engineering standards emphasizing precision, reliability, security, and efficiency.

## Architecture

The module provisions:
- **EKS Cluster**: Kubernetes 1.28+ with comprehensive logging and monitoring
- **Multi-AZ VPC**: Secure network architecture with public/private subnets
- **Node Groups**: Mixed instance types with spot instances for cost optimization
- **Security**: IAM roles, security groups, encryption, and compliance features
- **Add-ons**: AWS Load Balancer Controller, Cluster Autoscaler, EBS/EFS CSI drivers
- **Monitoring**: CloudWatch integration with custom metrics for Epic 8 services

## Swiss Engineering Standards

### Precision
- Exact resource allocation with environment-specific scaling
- Fine-tuned autoscaling parameters for >70% resource utilization
- Comprehensive tagging and resource organization

### Reliability
- Multi-AZ deployment for 99.9% uptime capability
- Automatic failover and self-healing mechanisms
- Comprehensive health checks and monitoring

### Security
- Three security levels: basic, enhanced, maximum
- Encryption at rest and in transit
- Network segmentation with private clusters
- IAM roles with least privilege access

### Efficiency
- Cost optimization with spot instances (configurable percentage)
- Right-sizing based on environment (dev/staging/prod)
- Resource quotas and limits enforcement

## Usage

### Basic Usage

```hcl
module "epic8_eks" {
  source = "./modules/aws-eks"

  project_name = "epic8-rag"
  environment  = "prod"
  region       = "eu-central-1"

  # Swiss compliance
  swiss_compliance_enabled   = true
  data_residency_enforcement = true
  security_level            = "enhanced"

  # Cost optimization
  enable_spot_instances     = true
  spot_instance_percentage  = 40
  single_nat_gateway       = false  # High availability for prod

  # Epic 8 platform deployment
  deploy_epic8_platform    = true
  epic8_helm_chart_version = "1.0.0"
  epic8_values_file       = "../../helm/epic8-platform/values-prod.yaml"

  # Additional tags
  additional_tags = {
    Team        = "platform-engineering"
    CostCenter  = "engineering"
    Environment = "production"
  }
}
```

### Advanced Configuration

```hcl
module "epic8_eks" {
  source = "./modules/aws-eks"

  project_name = "epic8-rag"
  environment  = "prod"
  region       = "eu-central-1"

  # Network configuration
  vpc_cidr             = "10.0.0.0/16"
  private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  # Security configuration
  security_level                         = "maximum"
  cluster_endpoint_private_access        = true
  cluster_endpoint_public_access         = true
  cluster_endpoint_public_access_cidrs   = ["203.0.113.0/24"]  # Your office IP

  # Custom node groups
  node_groups = {
    general = {
      instance_types = ["m5.large", "m5.xlarge"]
      scaling_config = {
        desired_size = 3
        max_size     = 10
        min_size     = 1
      }
      update_config = {
        max_unavailable_percentage = 25
      }
      capacity_type = "ON_DEMAND"
      ami_type      = "AL2_x86_64"
      disk_size     = 50
      labels = {
        "epic8.io/node-type" = "general"
        "epic8.io/workload"  = "api-services"
      }
      taints = []
    }

    ml_workloads = {
      instance_types = ["r5.xlarge", "r5.2xlarge"]
      scaling_config = {
        desired_size = 2
        max_size     = 6
        min_size     = 0
      }
      update_config = {
        max_unavailable_percentage = 25
      }
      capacity_type = "ON_DEMAND"
      ami_type      = "AL2_x86_64"
      disk_size     = 100
      labels = {
        "epic8.io/node-type" = "ml-workloads"
        "epic8.io/high-memory" = "true"
      }
      taints = [{
        key    = "workload.epic8.io/ml"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  # Add-ons configuration
  enable_aws_load_balancer_controller = true
  enable_cluster_autoscaler          = true
  enable_metrics_server              = true
  enable_ebs_csi_driver             = true
  enable_efs_csi_driver             = false

  # Monitoring
  enable_cluster_logging = true
  log_retention_days     = 30

  additional_tags = {
    Team       = "platform-engineering"
    CostCenter = "engineering"
    Project    = "epic8-rag-platform"
  }
}
```

## Swiss Region Preferences

The module is optimized for Swiss/EU deployments:

1. **Primary Region**: `eu-central-1` (Frankfurt) - Closest to Switzerland
2. **Secondary Region**: `eu-west-1` (Ireland) - EU GDPR compliant fallback
3. **GDPR Compliance**: Automatic data residency enforcement
4. **Swiss Data Protection**: Enhanced security configurations

## Cost Optimization Features

### Spot Instances
- Configurable spot instance percentage (0-100%)
- Intelligent instance type mixing
- Environment-specific spot usage:
  - **Development**: 80% spot instances
  - **Staging**: 60% spot instances
  - **Production**: 40% spot instances

### Right-Sizing
- Environment-specific resource allocation
- Automatic scaling based on workload patterns
- Resource quotas and limits enforcement

### Network Optimization
- Single NAT Gateway option for non-production environments
- VPC endpoints for cost-effective AWS service access
- Efficient subnet allocation

## Security Features

### Three Security Levels

#### Basic Security
- Standard AWS security groups
- Basic encryption for EBS volumes
- Public cluster endpoint with CIDR restrictions

#### Enhanced Security (Default)
- KMS encryption for secrets and EBS volumes
- VPC Flow Logs enabled
- Private cluster endpoint access
- Enhanced security groups with strict rules

#### Maximum Security
- Customer-managed KMS keys with rotation
- VPC endpoints for all AWS services
- Private-only cluster endpoint
- Pod Security Standards enforcement
- Network policies enabled

### Compliance Features
- GDPR compliance configurations
- Swiss data residency enforcement
- Audit logging for all cluster activities
- Comprehensive resource tagging for compliance tracking

## Monitoring and Observability

### CloudWatch Integration
- EKS cluster logs (API, audit, authenticator, controllerManager, scheduler)
- Custom metrics for Epic 8 services
- Enhanced node monitoring with CloudWatch agent

### Epic 8 Specific Monitoring
- Service-level metrics collection
- Performance monitoring for ML workloads
- Cost tracking with detailed tagging
- Health checks for all Epic 8 services

## Epic 8 Platform Integration

### Automatic Deployment
The module can automatically deploy the Epic 8 platform using Helm:

```hcl
deploy_epic8_platform    = true
epic8_helm_chart_version = "1.0.0"
epic8_values_file       = "path/to/values.yaml"
```

### Service Configuration
- **API Gateway**: Auto-scaling based on demand
- **Query Analyzer**: Optimized for ML workloads with dedicated node pools
- **Retriever Service**: Persistent storage with performance optimization
- **Generator Service**: Multi-model support with resource allocation
- **Cache Service**: Redis cluster with high availability
- **Analytics Service**: Prometheus and Grafana integration

## Prerequisites

### AWS Requirements
- AWS CLI configured with appropriate permissions
- Terraform >= 1.5.0
- kubectl for cluster management

### Required AWS Permissions
- EKS cluster and node group management
- VPC and networking resources
- IAM role and policy management
- CloudWatch logs and metrics
- EC2 instances and security groups

### Swiss Compliance Prerequisites
- Ensure your AWS account has access to eu-central-1 region
- Configure appropriate data classification and handling procedures
- Implement organization-specific compliance monitoring

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project_name | Name of the Epic 8 RAG platform project | `string` | `"epic8-rag"` | no |
| environment | Environment name (dev, staging, prod) | `string` | n/a | yes |
| region | AWS region for deployment | `string` | `"eu-central-1"` | no |
| swiss_compliance_enabled | Enable Swiss/GDPR compliance configurations | `bool` | `true` | no |
| security_level | Security level: basic, enhanced, maximum | `string` | `"enhanced"` | no |
| enable_spot_instances | Enable spot instances for cost optimization | `bool` | `true` | no |
| spot_instance_percentage | Percentage of spot instances | `number` | `50` | no |
| deploy_epic8_platform | Deploy Epic 8 platform via Helm | `bool` | `false` | no |

## Outputs

| Name | Description |
|------|-------------|
| cluster_name | EKS cluster name |
| cluster_endpoint | EKS cluster API server endpoint |
| cluster_arn | EKS cluster ARN |
| vpc_id | VPC ID where the cluster is deployed |
| kubeconfig_command | Command to update kubeconfig |
| swiss_compliance_status | Swiss compliance configuration status |
| cost_optimization | Cost optimization configuration |

## Examples

See the `examples/` directory for complete deployment scenarios:
- `multi-cloud-deployment/` - Multi-cloud Epic 8 deployment
- `swiss-compliant-setup/` - Maximum Swiss compliance configuration
- `cost-optimized-deployment/` - Development environment with cost optimization

## Roadmap

### Planned Features
- Integration with AWS App Mesh for advanced service mesh capabilities
- Support for Graviton2/Graviton3 instances for better price-performance
- Advanced auto-scaling with custom metrics from Epic 8 services
- Integration with AWS X-Ray for distributed tracing

### Swiss Market Enhancements
- Integration with Swiss identity providers
- Support for Swiss financial services compliance frameworks
- Enhanced data sovereignty features

## Support

For issues related to this module:
1. Check the [troubleshooting guide](./docs/troubleshooting.md)
2. Review the [FAQ](./docs/faq.md)
3. Open an issue with detailed logs and configuration

## License

This module is licensed under the MIT License. See [LICENSE](./LICENSE) for full details.