# EKS Cluster Configuration
# Swiss Engineering Standards: High Availability, Security, Monitoring

# CloudWatch Log Group for EKS cluster logs
resource "aws_cloudwatch_log_group" "eks" {
  name              = "/aws/eks/${local.cluster_name}/cluster"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.security_level == "maximum" ? aws_kms_key.eks[0].arn : null

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-logs"
    Service = "eks-cluster"
  })
}

# KMS key for EKS encryption (maximum security level)
resource "aws_kms_key" "eks" {
  count = var.security_level == "maximum" ? 1 : 0

  description             = "EKS Secret Encryption Key for ${local.cluster_name}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-kms-key"
    Service = "eks-encryption"
  })
}

resource "aws_kms_alias" "eks" {
  count = var.security_level == "maximum" ? 1 : 0

  name          = "alias/${local.cluster_name}-eks"
  target_key_id = aws_kms_key.eks[0].key_id
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = local.cluster_name
  version  = var.kubernetes_version
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids              = concat(module.vpc.private_subnets, module.vpc.public_subnets)
    endpoint_private_access = var.cluster_endpoint_private_access
    endpoint_public_access  = var.cluster_endpoint_public_access
    public_access_cidrs     = var.cluster_endpoint_public_access_cidrs
    security_group_ids      = [aws_security_group.eks_cluster.id]
  }

  # Encryption configuration for secrets (enhanced/maximum security)
  dynamic "encryption_config" {
    for_each = var.security_level != "basic" ? [1] : []
    content {
      provider {
        key_arn = var.security_level == "maximum" ? aws_kms_key.eks[0].arn : "alias/aws/eks"
      }
      resources = ["secrets"]
    }
  }

  # Enable logging for all control plane components
  enabled_cluster_log_types = var.enable_cluster_logging ? var.cluster_log_types : []

  # Ensure proper ordering
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_AmazonEKSClusterPolicy,
    aws_cloudwatch_log_group.eks,
  ]

  tags = merge(local.common_tags, {
    Name = local.cluster_name
    Type = "eks-cluster"
  })
}

# OIDC Identity Provider for IRSA (IAM Roles for Service Accounts)
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-oidc"
    Service = "eks-irsa"
  })
}

# Security group for EKS cluster
resource "aws_security_group" "eks_cluster" {
  name_prefix = "${local.cluster_name}-cluster-"
  vpc_id      = module.vpc.vpc_id
  description = "EKS cluster security group"

  # HTTPS API server access
  ingress {
    description = "EKS API Server"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.cluster_endpoint_public_access_cidrs
  }

  # Allow all outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-cluster-sg"
    Type = "eks-cluster-security"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Additional security group rules for node communication
resource "aws_security_group_rule" "cluster_ingress_node_https" {
  description              = "Allow pods to communicate with the cluster API Server"
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.eks_cluster.id
  source_security_group_id = aws_security_group.eks_node_group.id
  to_port                  = 443
  type                     = "ingress"
}

# EKS Add-ons
resource "aws_eks_addon" "main" {
  for_each = local.eks_addons

  cluster_name             = aws_eks_cluster.main.name
  addon_name               = each.key
  addon_version            = each.value.version
  resolve_conflicts        = "OVERWRITE"
  service_account_role_arn = each.value.service_account_role_arn

  depends_on = [
    aws_eks_node_group.main,
  ]

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-${each.key}"
    Type = "eks-addon"
  })
}

# Local values for add-ons configuration
locals {
  eks_addons = merge(
    # Core Add-ons
    {
      "kube-proxy" = {
        version                  = data.aws_eks_addon_version.kube_proxy.version
        service_account_role_arn = null
      }
      "vpc-cni" = {
        version                  = data.aws_eks_addon_version.vpc_cni.version
        service_account_role_arn = null
      }
      "coredns" = {
        version                  = data.aws_eks_addon_version.coredns.version
        service_account_role_arn = null
      }
    },
    # EBS CSI Driver (conditional)
    var.enable_ebs_csi_driver ? {
      "aws-ebs-csi-driver" = {
        version                  = data.aws_eks_addon_version.ebs_csi[0].version
        service_account_role_arn = aws_iam_role.ebs_csi_driver[0].arn
      }
    } : {},
    # EFS CSI Driver (conditional)
    var.enable_efs_csi_driver ? {
      "aws-efs-csi-driver" = {
        version                  = data.aws_eks_addon_version.efs_csi[0].version
        service_account_role_arn = aws_iam_role.efs_csi_driver[0].arn
      }
    } : {}
  )
}

# Data sources for latest add-on versions
data "aws_eks_addon_version" "kube_proxy" {
  addon_name         = "kube-proxy"
  kubernetes_version = aws_eks_cluster.main.version
  most_recent        = true
}

data "aws_eks_addon_version" "vpc_cni" {
  addon_name         = "vpc-cni"
  kubernetes_version = aws_eks_cluster.main.version
  most_recent        = true
}

data "aws_eks_addon_version" "coredns" {
  addon_name         = "coredns"
  kubernetes_version = aws_eks_cluster.main.version
  most_recent        = true
}

data "aws_eks_addon_version" "ebs_csi" {
  count = var.enable_ebs_csi_driver ? 1 : 0

  addon_name         = "aws-ebs-csi-driver"
  kubernetes_version = aws_eks_cluster.main.version
  most_recent        = true
}

data "aws_eks_addon_version" "efs_csi" {
  count = var.enable_efs_csi_driver ? 1 : 0

  addon_name         = "aws-efs-csi-driver"
  kubernetes_version = aws_eks_cluster.main.version
  most_recent        = true
}