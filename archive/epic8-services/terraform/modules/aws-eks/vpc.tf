# AWS VPC Configuration for EKS
# Swiss Engineering Standards: Secure, Efficient Network Architecture

# VPC Module using AWS VPC Terraform module
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.cluster_name}-vpc"
  cidr = var.vpc_cidr

  # Availability zones for multi-AZ deployment (Swiss reliability standards)
  azs = slice(data.aws_availability_zones.available.names, 0, 3)

  # Private subnets for worker nodes (security best practice)
  private_subnets = var.private_subnet_cidrs

  # Public subnets for load balancers and NAT gateways
  public_subnets = var.public_subnet_cidrs

  # NAT Gateway configuration for cost optimization
  enable_nat_gateway   = var.enable_nat_gateway
  single_nat_gateway   = var.single_nat_gateway && var.environment != "prod"
  one_nat_gateway_per_az = var.environment == "prod" && !var.single_nat_gateway

  # Internet Gateway for public connectivity
  enable_igw = true

  # DNS configuration for EKS requirements
  enable_dns_hostnames = true
  enable_dns_support   = true

  # VPC Flow Logs for security monitoring
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true
  flow_log_cloudwatch_log_group_retention_in_days = var.log_retention_days

  # Public subnet tags for AWS Load Balancer Controller
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }

  # Private subnet tags for internal load balancers
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }

  # VPC tags for EKS cluster discovery
  tags = merge(local.common_tags, {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    Name = "${local.cluster_name}-vpc"
    NetworkType = "eks-cluster"
    SwissCompliance = var.swiss_compliance_enabled ? "enabled" : "disabled"
  })
}

# VPC Endpoints for cost optimization and security
resource "aws_vpc_endpoint" "s3" {
  count = var.security_level != "basic" ? 1 : 0

  vpc_id       = module.vpc.vpc_id
  service_name = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = concat(
    module.vpc.private_route_table_ids,
    module.vpc.public_route_table_ids
  )

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-s3-endpoint"
    Service = "s3"
  })
}

resource "aws_vpc_endpoint" "ec2" {
  count = var.security_level == "maximum" ? 1 : 0

  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.region}.ec2"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]

  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-ec2-endpoint"
    Service = "ec2"
  })
}

resource "aws_vpc_endpoint" "ecr_api" {
  count = var.security_level == "maximum" ? 1 : 0

  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]

  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-ecr-api-endpoint"
    Service = "ecr-api"
  })
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  count = var.security_level == "maximum" ? 1 : 0

  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]

  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-ecr-dkr-endpoint"
    Service = "ecr-dkr"
  })
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  count = var.security_level == "maximum" ? 1 : 0

  name_prefix = "${local.cluster_name}-vpc-endpoints-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for VPC endpoints"

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-vpc-endpoints-sg"
    Type = "vpc-endpoints"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Additional security group for Epic 8 services
resource "aws_security_group" "epic8_services" {
  name_prefix = "${local.cluster_name}-epic8-services-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for Epic 8 RAG platform services"

  # HTTP traffic for internal services
  ingress {
    description = "HTTP from VPC"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # HTTPS traffic for external access
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # gRPC traffic for service communication
  ingress {
    description = "gRPC from VPC"
    from_port   = 8080
    to_port     = 8090
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Redis cache traffic
  ingress {
    description = "Redis from VPC"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Prometheus metrics
  ingress {
    description = "Metrics from VPC"
    from_port   = 9090
    to_port     = 9099
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.cluster_name}-epic8-services-sg"
    Type = "application-services"
    Platform = "epic8-rag"
  })

  lifecycle {
    create_before_destroy = true
  }
}