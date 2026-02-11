# EKS Node Groups Configuration
# Swiss Engineering Standards: Cost-Optimized, High-Performance, Reliable

# Security group for worker nodes
resource "aws_security_group" "eks_node_group" {
  name_prefix = "${local.cluster_name}-node-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for EKS worker nodes"

  # Allow nodes to communicate with each other
  ingress {
    description = "Node to node communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  # Allow pods to communicate with the cluster API Server
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-node-sg"
    Type = "eks-node-security"
    "kubernetes.io/cluster/${local.cluster_name}" = "owned"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Additional security group rules for node groups
resource "aws_security_group_rule" "node_ingress_self" {
  description              = "Allow node to communicate with each other"
  from_port                = 0
  protocol                 = "-1"
  security_group_id        = aws_security_group.eks_node_group.id
  source_security_group_id = aws_security_group.eks_node_group.id
  to_port                  = 65535
  type                     = "ingress"
}

resource "aws_security_group_rule" "node_ingress_cluster" {
  description              = "Allow worker Kubelets and pods to receive communication from the cluster control plane"
  from_port                = 1025
  protocol                 = "tcp"
  security_group_id        = aws_security_group.eks_node_group.id
  source_security_group_id = aws_security_group.eks_cluster.id
  to_port                  = 65535
  type                     = "ingress"
}

# Launch template for custom node configuration
resource "aws_launch_template" "node_group" {
  for_each = local.node_group_configs

  name_prefix   = "${local.cluster_name}-${each.key}-"
  instance_type = each.value.instance_types[0]

  vpc_security_group_ids = [aws_security_group.eks_node_group.id]

  # User data for node initialization
  user_data = base64encode(templatefile("${path.module}/templates/user-data.sh", {
    cluster_name        = aws_eks_cluster.main.name
    cluster_endpoint    = aws_eks_cluster.main.endpoint
    cluster_ca          = aws_eks_cluster.main.certificate_authority[0].data
    bootstrap_arguments = each.value.bootstrap_arguments
  }))

  # EBS optimization
  ebs_optimized = true

  # Block device mappings for node storage
  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = each.value.disk_size
      volume_type           = "gp3"
      iops                  = each.value.disk_size * 3
      throughput            = min(each.value.disk_size * 0.25, 1000)
      encrypted             = var.security_level != "basic"
      kms_key_id           = var.security_level == "maximum" ? aws_kms_key.ebs[0].arn : null
      delete_on_termination = true
    }
  }

  # Instance metadata service configuration
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
    instance_metadata_tags      = "enabled"
  }

  # Monitoring
  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(local.common_tags, {
      Name = "${local.cluster_name}-${each.key}-node"
      NodeGroup = each.key
      "kubernetes.io/cluster/${local.cluster_name}" = "owned"
    })
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-${each.key}-template"
  })
}

# KMS key for EBS encryption (maximum security)
resource "aws_kms_key" "ebs" {
  count = var.security_level == "maximum" ? 1 : 0

  description             = "EBS encryption key for ${local.cluster_name}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-ebs-kms"
    Service = "ebs-encryption"
  })
}

resource "aws_kms_alias" "ebs" {
  count = var.security_level == "maximum" ? 1 : 0

  name          = "alias/${local.cluster_name}-ebs"
  target_key_id = aws_kms_key.ebs[0].key_id
}

# EKS Node Groups
resource "aws_eks_node_group" "main" {
  for_each = local.node_group_configs

  cluster_name    = aws_eks_cluster.main.name
  node_group_name = each.key
  node_role_arn   = aws_iam_role.eks_node_group.arn
  subnet_ids      = module.vpc.private_subnets

  # Instance configuration
  capacity_type  = each.value.capacity_type
  instance_types = each.value.instance_types
  ami_type       = each.value.ami_type
  disk_size      = each.value.disk_size

  # Launch template
  launch_template {
    id      = aws_launch_template.node_group[each.key].id
    version = aws_launch_template.node_group[each.key].latest_version
  }

  # Scaling configuration
  scaling_config {
    desired_size = each.value.scaling_config.desired_size
    max_size     = each.value.scaling_config.max_size
    min_size     = each.value.scaling_config.min_size
  }

  # Update configuration
  update_config {
    max_unavailable_percentage = each.value.update_config.max_unavailable_percentage
  }

  # Labels
  labels = merge(each.value.labels, {
    "epic8.io/node-group" = each.key
    "epic8.io/environment" = var.environment
    "epic8.io/workload-type" = each.value.workload_type
  })

  # Taints
  dynamic "taint" {
    for_each = each.value.taints
    content {
      key    = taint.value.key
      value  = taint.value.value
      effect = taint.value.effect
    }
  }

  # Ensure proper ordering
  depends_on = [
    aws_iam_role_policy_attachment.eks_node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.eks_node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.eks_node_group_AmazonEC2ContainerRegistryReadOnly,
  ]

  # Lifecycle configuration
  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-${each.key}"
    NodeGroup = each.key
    WorkloadType = each.value.workload_type
  })
}

# Local values for node group configurations
locals {
  # Environment-specific node group configurations
  base_node_config = local.environment_configs[var.environment]

  node_group_configs = length(var.node_groups) > 0 ? var.node_groups : {
    # General purpose node group
    general = {
      instance_types = local.base_node_config.instance_types
      capacity_type  = var.enable_spot_instances ? "SPOT" : "ON_DEMAND"
      ami_type       = "AL2_x86_64"
      disk_size      = 50
      workload_type  = "general"

      scaling_config = {
        desired_size = local.base_node_config.desired_nodes
        max_size     = local.base_node_config.max_nodes
        min_size     = local.base_node_config.min_nodes
      }

      update_config = {
        max_unavailable_percentage = 25
      }

      labels = {
        "epic8.io/node-type" = "general"
        "epic8.io/spot-instance" = var.enable_spot_instances ? "true" : "false"
      }

      taints = []
      bootstrap_arguments = "--container-runtime containerd"
    }

    # High-memory node group for ML workloads
    ml-workloads = {
      instance_types = var.environment == "prod" ? ["r5.xlarge", "r5.2xlarge"] : ["r5.large"]
      capacity_type  = "ON_DEMAND"  # Critical ML workloads need stability
      ami_type       = "AL2_x86_64"
      disk_size      = 100
      workload_type  = "ml"

      scaling_config = {
        desired_size = var.environment == "prod" ? 2 : 1
        max_size     = var.environment == "prod" ? 6 : 3
        min_size     = var.environment == "prod" ? 1 : 0
      }

      update_config = {
        max_unavailable_percentage = 25
      }

      labels = {
        "epic8.io/node-type" = "ml-workloads"
        "epic8.io/high-memory" = "true"
        "workload.epic8.io/ml" = "true"
      }

      taints = [{
        key    = "workload.epic8.io/ml"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
      bootstrap_arguments = "--container-runtime containerd --kubelet-extra-args '--node-labels=workload.epic8.io/ml=true'"
    }

    # Spot instance node group for cost optimization
    spot-workloads = var.enable_spot_instances ? {
      instance_types = concat(local.base_node_config.instance_types, ["t3.xlarge", "c5.xlarge"])
      capacity_type  = "SPOT"
      ami_type       = "AL2_x86_64"
      disk_size      = 50
      workload_type  = "spot"

      scaling_config = {
        desired_size = 0
        max_size     = local.base_node_config.max_nodes
        min_size     = 0
      }

      update_config = {
        max_unavailable_percentage = 50  # Higher tolerance for spot instances
      }

      labels = {
        "epic8.io/node-type" = "spot-workloads"
        "epic8.io/spot-instance" = "true"
        "node.kubernetes.io/capacity-type" = "spot"
      }

      taints = [{
        key    = "epic8.io/spot-instance"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
      bootstrap_arguments = "--container-runtime containerd --kubelet-extra-args '--node-labels=node.kubernetes.io/capacity-type=spot'"
    } : {}
  }
}