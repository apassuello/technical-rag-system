# AWS EKS Module Outputs
# Swiss Engineering Standards: Comprehensive Information Export

# Cluster Information
output "cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.main.id
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "EKS cluster API server endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_version" {
  description = "EKS cluster Kubernetes version"
  value       = aws_eks_cluster.main.version
}

output "cluster_platform_version" {
  description = "EKS cluster platform version"
  value       = aws_eks_cluster.main.platform_version
}

output "cluster_status" {
  description = "EKS cluster status"
  value       = aws_eks_cluster.main.status
}

# Security Information
output "cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

output "oidc_provider_arn" {
  description = "ARN of the OIDC Provider for IRSA"
  value       = aws_iam_openid_connect_provider.eks.arn
}

# Network Information
output "vpc_id" {
  description = "VPC ID where the cluster is deployed"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnets
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = module.vpc.natgw_ids
}

# Node Group Information
output "node_groups" {
  description = "EKS node groups information"
  value = {
    for k, v in aws_eks_node_group.main : k => {
      arn           = v.arn
      status        = v.status
      capacity_type = v.capacity_type
      instance_types = v.instance_types
      scaling_config = v.scaling_config
      remote_access = v.remote_access
    }
  }
}

# IAM Information
output "cluster_iam_role_arn" {
  description = "IAM role ARN of the EKS cluster"
  value       = aws_iam_role.eks_cluster.arn
}

output "node_group_iam_role_arn" {
  description = "IAM role ARN of the EKS node groups"
  value       = aws_iam_role.eks_node_group.arn
}

# Add-on Information
output "eks_addons" {
  description = "Map of EKS add-ons and their versions"
  value = {
    for k, v in aws_eks_addon.main : k => {
      addon_version = v.addon_version
      status        = v.status
    }
  }
}

# Swiss Compliance Information
output "swiss_compliance_status" {
  description = "Swiss compliance configuration status"
  value = {
    enabled              = var.swiss_compliance_enabled
    data_residency       = var.data_residency_enforcement
    region               = var.region
    security_level       = var.security_level
    gdpr_compliant      = contains(["eu-central-1", "eu-west-1", "eu-west-2", "eu-west-3", "eu-north-1", "eu-south-1"], var.region)
  }
}

# Cost Optimization Information
output "cost_optimization" {
  description = "Cost optimization configuration"
  value = {
    spot_instances_enabled = var.enable_spot_instances
    spot_percentage       = var.spot_instance_percentage
    single_nat_gateway    = var.single_nat_gateway
    environment           = var.environment
  }
}

# Monitoring Information
output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name for EKS cluster logs"
  value       = aws_cloudwatch_log_group.eks.name
}

output "cloudwatch_log_group_arn" {
  description = "CloudWatch log group ARN for EKS cluster logs"
  value       = aws_cloudwatch_log_group.eks.arn
}

# Kubeconfig Information
output "kubeconfig_command" {
  description = "Command to update kubeconfig for this cluster"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${aws_eks_cluster.main.name}"
}

# Epic 8 Platform Information
output "epic8_platform_deployed" {
  description = "Whether Epic 8 platform is deployed"
  value       = var.deploy_epic8_platform
}

output "epic8_helm_release_name" {
  description = "Epic 8 Helm release name"
  value       = var.deploy_epic8_platform ? helm_release.epic8_platform[0].name : null
}

output "epic8_helm_release_status" {
  description = "Epic 8 Helm release status"
  value       = var.deploy_epic8_platform ? helm_release.epic8_platform[0].status : null
}

# Load Balancer Information
output "load_balancer_controller_service_account" {
  description = "AWS Load Balancer Controller service account information"
  value = var.enable_aws_load_balancer_controller ? {
    name      = kubernetes_service_account.aws_load_balancer_controller[0].metadata[0].name
    namespace = kubernetes_service_account.aws_load_balancer_controller[0].metadata[0].namespace
  } : null
}

# Cluster Autoscaler Information
output "cluster_autoscaler_service_account" {
  description = "Cluster Autoscaler service account information"
  value = var.enable_cluster_autoscaler ? {
    name      = kubernetes_service_account.cluster_autoscaler[0].metadata[0].name
    namespace = kubernetes_service_account.cluster_autoscaler[0].metadata[0].namespace
  } : null
}

# Resource Tags
output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# Connection Information for Epic 8 Services
output "epic8_connection_info" {
  description = "Connection information for Epic 8 services"
  value = {
    cluster_endpoint     = aws_eks_cluster.main.endpoint
    region              = var.region
    cluster_name        = aws_eks_cluster.main.name
    vpc_id              = module.vpc.vpc_id
    private_subnet_ids  = module.vpc.private_subnets
    security_group_id   = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
  }
  sensitive = false
}