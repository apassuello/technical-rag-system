# EKS Add-ons and Essential Services Configuration
# Swiss Engineering Standards: Automated Deployment, Monitoring, Security

# Configure Kubernetes and Helm providers
data "aws_eks_cluster_auth" "cluster" {
  name = aws_eks_cluster.main.name
}

provider "kubernetes" {
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = aws_eks_cluster.main.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# Service Account for AWS Load Balancer Controller
resource "kubernetes_service_account" "aws_load_balancer_controller" {
  count = var.enable_aws_load_balancer_controller ? 1 : 0

  metadata {
    name      = "aws-load-balancer-controller"
    namespace = "kube-system"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.aws_load_balancer_controller[0].arn
    }
    labels = {
      "app.kubernetes.io/name"       = "aws-load-balancer-controller"
      "app.kubernetes.io/component"  = "controller"
      "app.kubernetes.io/managed-by" = "terraform"
      "epic8.io/service"            = "load-balancer-controller"
    }
  }

  depends_on = [aws_eks_node_group.main]
}

# AWS Load Balancer Controller Helm Chart
resource "helm_release" "aws_load_balancer_controller" {
  count = var.enable_aws_load_balancer_controller ? 1 : 0

  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.6.2"

  set {
    name  = "clusterName"
    value = aws_eks_cluster.main.name
  }

  set {
    name  = "serviceAccount.create"
    value = "false"
  }

  set {
    name  = "serviceAccount.name"
    value = kubernetes_service_account.aws_load_balancer_controller[0].metadata[0].name
  }

  set {
    name  = "region"
    value = var.region
  }

  set {
    name  = "vpcId"
    value = module.vpc.vpc_id
  }

  # Swiss engineering: comprehensive monitoring
  set {
    name  = "enableServiceMutatorWebhook"
    value = "false"
  }

  set {
    name  = "logLevel"
    value = "info"
  }

  depends_on = [
    aws_eks_node_group.main,
    kubernetes_service_account.aws_load_balancer_controller
  ]
}

# Service Account for Cluster Autoscaler
resource "kubernetes_service_account" "cluster_autoscaler" {
  count = var.enable_cluster_autoscaler ? 1 : 0

  metadata {
    name      = "cluster-autoscaler"
    namespace = "kube-system"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.cluster_autoscaler[0].arn
    }
    labels = {
      "app.kubernetes.io/name"       = "cluster-autoscaler"
      "app.kubernetes.io/component"  = "autoscaler"
      "app.kubernetes.io/managed-by" = "terraform"
      "epic8.io/service"            = "cluster-autoscaler"
    }
  }

  depends_on = [aws_eks_node_group.main]
}

# Cluster Autoscaler Helm Chart
resource "helm_release" "cluster_autoscaler" {
  count = var.enable_cluster_autoscaler ? 1 : 0

  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  namespace  = "kube-system"
  version    = "9.29.0"

  set {
    name  = "autoDiscovery.clusterName"
    value = aws_eks_cluster.main.name
  }

  set {
    name  = "awsRegion"
    value = var.region
  }

  set {
    name  = "rbac.serviceAccount.create"
    value = "false"
  }

  set {
    name  = "rbac.serviceAccount.name"
    value = kubernetes_service_account.cluster_autoscaler[0].metadata[0].name
  }

  # Swiss engineering: precise scaling parameters
  set {
    name  = "extraArgs.scale-down-delay-after-add"
    value = "10m"
  }

  set {
    name  = "extraArgs.scale-down-unneeded-time"
    value = "10m"
  }

  set {
    name  = "extraArgs.scale-down-utilization-threshold"
    value = "0.7"
  }

  set {
    name  = "extraArgs.skip-nodes-with-local-storage"
    value = "false"
  }

  # Resource management
  set {
    name  = "resources.limits.cpu"
    value = "100m"
  }

  set {
    name  = "resources.limits.memory"
    value = "300Mi"
  }

  set {
    name  = "resources.requests.cpu"
    value = "100m"
  }

  set {
    name  = "resources.requests.memory"
    value = "300Mi"
  }

  depends_on = [
    aws_eks_node_group.main,
    kubernetes_service_account.cluster_autoscaler
  ]
}

# Metrics Server (if enabled)
resource "helm_release" "metrics_server" {
  count = var.enable_metrics_server ? 1 : 0

  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  namespace  = "kube-system"
  version    = "3.11.0"

  set {
    name  = "args"
    value = "{--kubelet-insecure-tls,--kubelet-preferred-address-types=InternalIP}"
  }

  # Resource management for Swiss efficiency
  set {
    name  = "resources.limits.cpu"
    value = "100m"
  }

  set {
    name  = "resources.limits.memory"
    value = "200Mi"
  }

  set {
    name  = "resources.requests.cpu"
    value = "100m"
  }

  set {
    name  = "resources.requests.memory"
    value = "200Mi"
  }

  depends_on = [aws_eks_node_group.main]
}

# Epic 8 Platform Deployment (conditional)
resource "helm_release" "epic8_platform" {
  count = var.deploy_epic8_platform ? 1 : 0

  name       = "epic8-platform"
  chart      = var.epic8_values_file != "" ? "../../../helm/epic8-platform" : "https://github.com/your-org/epic8-platform/releases/download/v${var.epic8_helm_chart_version}/epic8-platform-${var.epic8_helm_chart_version}.tgz"
  namespace  = "epic8"
  version    = var.epic8_helm_chart_version

  create_namespace = true
  wait             = true
  timeout          = 600

  # Environment-specific values
  values = var.epic8_values_file != "" ? [
    file(var.epic8_values_file)
  ] : [
    yamlencode({
      global = {
        environment     = var.environment
        clusterName    = aws_eks_cluster.main.name
        region         = var.region
        swissCompliance = var.swiss_compliance_enabled
      }

      # Service configurations optimized for Swiss performance standards
      services = {
        apiGateway = {
          replicaCount = var.environment == "prod" ? 3 : 2
          resources = {
            requests = {
              cpu    = var.environment == "prod" ? "200m" : "100m"
              memory = var.environment == "prod" ? "256Mi" : "128Mi"
            }
            limits = {
              cpu    = var.environment == "prod" ? "500m" : "250m"
              memory = var.environment == "prod" ? "512Mi" : "256Mi"
            }
          }
        }

        queryAnalyzer = {
          replicaCount = var.environment == "prod" ? 2 : 1
          nodeSelector = {
            "workload.epic8.io/ml" = "true"
          }
          tolerations = [{
            key      = "workload.epic8.io/ml"
            operator = "Equal"
            value    = "true"
            effect   = "NoSchedule"
          }]
        }

        retriever = {
          replicaCount = var.environment == "prod" ? 3 : 2
          persistence = {
            enabled = true
            size    = var.environment == "prod" ? "100Gi" : "50Gi"
          }
        }

        generator = {
          replicaCount = var.environment == "prod" ? 2 : 1
          resources = {
            requests = {
              cpu    = var.environment == "prod" ? "500m" : "250m"
              memory = var.environment == "prod" ? "1Gi" : "512Mi"
            }
            limits = {
              cpu    = var.environment == "prod" ? "2" : "1"
              memory = var.environment == "prod" ? "4Gi" : "2Gi"
            }
          }
        }

        cache = {
          redis = {
            enabled = true
            cluster = {
              enabled = var.environment == "prod"
              nodes   = var.environment == "prod" ? 3 : 1
            }
            persistence = {
              enabled = true
              size    = var.environment == "prod" ? "20Gi" : "10Gi"
            }
          }
        }

        analytics = {
          prometheus = {
            enabled = true
            retention = var.environment == "prod" ? "30d" : "7d"
            storage = {
              size = var.environment == "prod" ? "50Gi" : "20Gi"
            }
          }
          grafana = {
            enabled = true
            persistence = {
              enabled = true
              size    = "10Gi"
            }
          }
        }
      }

      # Ingress configuration for Swiss accessibility
      ingress = {
        enabled     = true
        className   = "alb"
        annotations = {
          "kubernetes.io/ingress.class"                    = "alb"
          "alb.ingress.kubernetes.io/scheme"              = "internet-facing"
          "alb.ingress.kubernetes.io/target-type"         = "ip"
          "alb.ingress.kubernetes.io/ssl-redirect"        = "443"
          "alb.ingress.kubernetes.io/certificate-arn"     = "arn:aws:acm:${var.region}:*:certificate/*"
          "alb.ingress.kubernetes.io/wafv2-acl-arn"      = "arn:aws:wafv2:${var.region}:*:global/webacl/epic8-waf/*"
          "alb.ingress.kubernetes.io/security-groups"     = aws_security_group.epic8_services.id
        }
        hosts = [
          {
            host = var.environment == "prod" ? "epic8.yourdomain.com" : "${var.environment}-epic8.yourdomain.com"
            paths = [
              {
                path     = "/"
                pathType = "Prefix"
                backend = {
                  service = {
                    name = "api-gateway"
                    port = {
                      number = 80
                    }
                  }
                }
              }
            ]
          }
        ]
      }

      # Security and compliance configurations
      security = {
        networkPolicies = {
          enabled = var.security_level != "basic"
        }
        podSecurityStandards = {
          enabled = var.security_level != "basic"
          level   = var.security_level == "maximum" ? "restricted" : "baseline"
        }
        serviceMonitor = {
          enabled = true
        }
      }
    })
  ]

  depends_on = [
    aws_eks_node_group.main,
    helm_release.aws_load_balancer_controller,
    helm_release.metrics_server
  ]
}

# Namespace for Epic 8 monitoring
resource "kubernetes_namespace" "epic8_monitoring" {
  metadata {
    name = "epic8-monitoring"
    labels = {
      "name"                        = "epic8-monitoring"
      "app.kubernetes.io/managed-by" = "terraform"
      "epic8.io/component"          = "monitoring"
    }
  }

  depends_on = [aws_eks_node_group.main]
}

# Storage classes for different workload types
resource "kubernetes_storage_class" "epic8_fast" {
  metadata {
    name = "epic8-fast"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
    labels = {
      "epic8.io/storage-tier" = "fast"
      "epic8.io/workload"     = "ml-models"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    type      = "gp3"
    iops      = "3000"
    throughput = "125"
    encrypted = var.security_level != "basic" ? "true" : "false"
    kmsKeyId  = var.security_level == "maximum" ? aws_kms_key.ebs[0].arn : ""
  }

  depends_on = [aws_eks_addon.main]
}

resource "kubernetes_storage_class" "epic8_standard" {
  metadata {
    name = "epic8-standard"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
    labels = {
      "epic8.io/storage-tier" = "standard"
      "epic8.io/workload"     = "general"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    type     = "gp3"
    encrypted = var.security_level != "basic" ? "true" : "false"
    kmsKeyId = var.security_level == "maximum" ? aws_kms_key.ebs[0].arn : ""
  }

  depends_on = [aws_eks_addon.main]
}