# AKS Add-ons and Essential Services Configuration
# Swiss Engineering Standards: Automated Deployment, Monitoring, Security

# Configure Kubernetes and Helm providers for AKS
data "azurerm_kubernetes_cluster" "main" {
  name                = azurerm_kubernetes_cluster.main.name
  resource_group_name = azurerm_kubernetes_cluster.main.resource_group_name
  depends_on         = [azurerm_kubernetes_cluster.main]
}

provider "kubernetes" {
  host                   = data.azurerm_kubernetes_cluster.main.kube_config.0.host
  client_certificate     = base64decode(data.azurerm_kubernetes_cluster.main.kube_config.0.client_certificate)
  client_key            = base64decode(data.azurerm_kubernetes_cluster.main.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(data.azurerm_kubernetes_cluster.main.kube_config.0.cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = data.azurerm_kubernetes_cluster.main.kube_config.0.host
    client_certificate     = base64decode(data.azurerm_kubernetes_cluster.main.kube_config.0.client_certificate)
    client_key            = base64decode(data.azurerm_kubernetes_cluster.main.kube_config.0.client_key)
    cluster_ca_certificate = base64decode(data.azurerm_kubernetes_cluster.main.kube_config.0.cluster_ca_certificate)
  }
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

  # Environment-specific values for AKS
  values = var.epic8_values_file != "" ? [
    file(var.epic8_values_file)
  ] : [
    yamlencode({
      global = {
        environment     = var.environment
        clusterName     = azurerm_kubernetes_cluster.main.name
        location        = var.location
        provider        = "azure"
        swissCompliance = var.swiss_compliance_enabled
        resourceGroup   = local.create_resource_group ? azurerm_resource_group.main[0].name : data.azurerm_resource_group.existing[0].name
      }

      # Service configurations optimized for AKS and Swiss performance standards
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
          nodeSelector = {
            "epic8.io/node-type" = "default"
          }
        }

        queryAnalyzer = {
          replicaCount = var.environment == "prod" ? 2 : 1
          nodeSelector = {
            "epic8.io/node-type" = "ml-workloads"
          }
          tolerations = [{
            key      = "epic8.io/ml-workload"
            operator = "Equal"
            value    = "true"
            effect   = "NoSchedule"
          }]
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

        retriever = {
          replicaCount = var.environment == "prod" ? 3 : 2
          persistence = {
            enabled      = true
            size         = var.environment == "prod" ? "100Gi" : "50Gi"
            storageClass = "epic8-fast"
          }
          nodeSelector = {
            "epic8.io/node-type" = "default"
          }
        }

        generator = {
          replicaCount = var.environment == "prod" ? 2 : 1
          nodeSelector = {
            "epic8.io/node-type" = "ml-workloads"
          }
          tolerations = [{
            key      = "epic8.io/ml-workload"
            operator = "Equal"
            value    = "true"
            effect   = "NoSchedule"
          }]
          resources = {
            requests = {
              cpu    = var.environment == "prod" ? "1" : "500m"
              memory = var.environment == "prod" ? "2Gi" : "1Gi"
            }
            limits = {
              cpu    = var.environment == "prod" ? "4" : "2"
              memory = var.environment == "prod" ? "8Gi" : "4Gi"
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
              enabled      = true
              size         = var.environment == "prod" ? "20Gi" : "10Gi"
              storageClass = "epic8-standard"
            }
            nodeSelector = {
              "epic8.io/node-type" = "default"
            }
          }
        }

        analytics = {
          prometheus = {
            enabled = true
            retention = var.environment == "prod" ? "30d" : "7d"
            storage = {
              size         = var.environment == "prod" ? "50Gi" : "20Gi"
              storageClass = "epic8-standard"
            }
            nodeSelector = {
              "epic8.io/node-type" = "default"
            }
          }
          grafana = {
            enabled = true
            persistence = {
              enabled      = true
              size         = "10Gi"
              storageClass = "epic8-standard"
            }
            nodeSelector = {
              "epic8.io/node-type" = "default"
            }
          }
        }
      }

      # Ingress configuration for AKS with Application Gateway
      ingress = {
        enabled     = true
        className   = "azure/application-gateway"
        annotations = {
          "kubernetes.io/ingress.class"                = "azure/application-gateway"
          "appgw.ingress.kubernetes.io/ssl-redirect"   = "true"
          "appgw.ingress.kubernetes.io/backend-protocol" = "http"
          "appgw.ingress.kubernetes.io/health-probe-path" = "/health"
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
        tls = [
          {
            secretName = "epic8-tls"
            hosts = [
              var.environment == "prod" ? "epic8.yourdomain.com" : "${var.environment}-epic8.yourdomain.com"
            ]
          }
        ]
      }

      # Security and compliance configurations for AKS
      security = {
        networkPolicies = {
          enabled = var.network_policy != ""
        }
        podSecurityStandards = {
          enabled = var.security_level != "basic"
          level   = var.security_level == "maximum" ? "restricted" : "baseline"
        }
        serviceMonitor = {
          enabled = var.enable_oms_agent
        }
        workloadIdentity = {
          enabled = var.enable_workload_identity
        }
        azureKeyVault = {
          enabled = var.enable_azure_keyvault_secrets_provider
        }
      }

      # AKS-specific configurations
      aks = {
        workloadIdentity = {
          enabled = var.enable_workload_identity
        }
        azurePolicy = {
          enabled = var.enable_azure_policy
        }
        nodeSelector = {
          "epic8.io/node-type" = "default"
        }
      }
    })
  ]

  depends_on = [
    azurerm_kubernetes_cluster_node_pool.additional,
    kubernetes_storage_class.epic8_fast,
    kubernetes_storage_class.epic8_standard
  ]
}

# Namespace for Epic 8 monitoring
resource "kubernetes_namespace" "epic8_monitoring" {
  metadata {
    name = "epic8-monitoring"
    labels = {
      "name"                         = "epic8-monitoring"
      "app.kubernetes.io/managed-by" = "terraform"
      "epic8.io/component"           = "monitoring"
    }
  }

  depends_on = [azurerm_kubernetes_cluster.main]
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

  storage_provisioner    = "disk.csi.azure.com"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    skuName             = "Premium_LRS"
    kind                = "Managed"
    cachingmode         = "ReadOnly"
    fsType              = "ext4"
    enableBursting      = "true"
  }

  depends_on = [azurerm_kubernetes_cluster.main]
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

  storage_provisioner    = "disk.csi.azure.com"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    skuName     = "StandardSSD_LRS"
    kind        = "Managed"
    cachingmode = "ReadOnly"
    fsType      = "ext4"
  }

  depends_on = [azurerm_kubernetes_cluster.main]
}

# Azure Files storage class for shared storage
resource "kubernetes_storage_class" "epic8_shared" {
  metadata {
    name = "epic8-shared"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
    labels = {
      "epic8.io/storage-tier" = "shared"
      "epic8.io/workload"     = "shared-data"
    }
  }

  storage_provisioner    = "file.csi.azure.com"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "Immediate"
  allow_volume_expansion = true

  parameters = {
    skuName = var.environment == "prod" ? "Premium_LRS" : "Standard_LRS"
    fsType  = "nfs"
  }

  depends_on = [azurerm_kubernetes_cluster.main]
}

# Horizontal Pod Autoscaler for Epic 8 services
resource "kubernetes_manifest" "epic8_hpa" {
  for_each = var.deploy_epic8_platform ? toset([
    "api-gateway",
    "query-analyzer",
    "retriever",
    "generator"
  ]) : toset([])

  manifest = {
    apiVersion = "autoscaling/v2"
    kind       = "HorizontalPodAutoscaler"
    metadata = {
      name      = "${each.key}-hpa"
      namespace = "epic8"
      labels = {
        "app.kubernetes.io/managed-by" = "terraform"
        "epic8.io/component"           = "autoscaling"
        "epic8.io/service"             = each.key
      }
    }
    spec = {
      scaleTargetRef = {
        apiVersion = "apps/v1"
        kind       = "Deployment"
        name       = each.key
      }
      minReplicas = var.environment == "prod" ? 2 : 1
      maxReplicas = var.environment == "prod" ? 10 : 5
      metrics = [
        {
          type = "Resource"
          resource = {
            name = "cpu"
            target = {
              type               = "Utilization"
              averageUtilization = 70
            }
          }
        },
        {
          type = "Resource"
          resource = {
            name = "memory"
            target = {
              type               = "Utilization"
              averageUtilization = 80
            }
          }
        }
      ]
      behavior = {
        scaleUp = {
          stabilizationWindowSeconds = 60
          policies = [
            {
              type          = "Percent"
              value         = 50
              periodSeconds = 60
            }
          ]
        }
        scaleDown = {
          stabilizationWindowSeconds = 300
          policies = [
            {
              type          = "Percent"
              value         = 25
              periodSeconds = 60
            }
          ]
        }
      }
    }
  }

  depends_on = [helm_release.epic8_platform]
}

# Vertical Pod Autoscaler (if enabled)
resource "kubernetes_manifest" "epic8_vpa" {
  for_each = var.deploy_epic8_platform && var.enable_vertical_pod_autoscaler ? toset([
    "api-gateway",
    "query-analyzer",
    "retriever",
    "generator"
  ]) : toset([])

  manifest = {
    apiVersion = "autoscaling.k8s.io/v1"
    kind       = "VerticalPodAutoscaler"
    metadata = {
      name      = "${each.key}-vpa"
      namespace = "epic8"
      labels = {
        "app.kubernetes.io/managed-by" = "terraform"
        "epic8.io/component"           = "autoscaling"
        "epic8.io/service"             = each.key
      }
    }
    spec = {
      targetRef = {
        apiVersion = "apps/v1"
        kind       = "Deployment"
        name       = each.key
      }
      updatePolicy = {
        updateMode = "Auto"
      }
      resourcePolicy = {
        containerPolicies = [
          {
            containerName = each.key
            minAllowed = {
              cpu    = "100m"
              memory = "128Mi"
            }
            maxAllowed = {
              cpu    = var.environment == "prod" ? "4" : "2"
              memory = var.environment == "prod" ? "8Gi" : "4Gi"
            }
            controlledResources = ["cpu", "memory"]
          }
        ]
      }
    }
  }

  depends_on = [helm_release.epic8_platform]
}

# KEDA ScaledObjects (if KEDA is enabled)
resource "kubernetes_manifest" "epic8_keda" {
  for_each = var.deploy_epic8_platform && var.enable_keda ? toset([
    "query-analyzer",
    "generator"
  ]) : toset([])

  manifest = {
    apiVersion = "keda.sh/v1alpha1"
    kind       = "ScaledObject"
    metadata = {
      name      = "${each.key}-keda"
      namespace = "epic8"
      labels = {
        "app.kubernetes.io/managed-by" = "terraform"
        "epic8.io/component"           = "autoscaling"
        "epic8.io/service"             = each.key
      }
    }
    spec = {
      scaleTargetRef = {
        name = each.key
      }
      minReplicaCount = var.environment == "prod" ? 1 : 0
      maxReplicaCount = var.environment == "prod" ? 10 : 5
      triggers = [
        {
          type = "prometheus"
          metadata = {
            serverAddress = "http://prometheus.epic8-monitoring.svc.cluster.local:9090"
            metricName    = "${each.key}_queue_length"
            threshold     = "5"
            query         = "sum(rate(${each.key}_requests_total[1m]))"
          }
        }
      ]
    }
  }

  depends_on = [helm_release.epic8_platform]
}

# Network policies for Epic 8 services (if network policy is enabled)
resource "kubernetes_network_policy" "epic8_network_policies" {
  for_each = var.deploy_epic8_platform && var.network_policy != "" ? toset([
    "api-gateway",
    "query-analyzer",
    "retriever",
    "generator",
    "cache",
    "analytics"
  ]) : toset([])

  metadata {
    name      = "${each.key}-network-policy"
    namespace = "epic8"
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "epic8.io/component"           = "network-security"
      "epic8.io/service"             = each.key
    }
  }

  spec {
    pod_selector {
      match_labels = {
        "app.kubernetes.io/name" = each.key
      }
    }

    policy_types = ["Ingress", "Egress"]

    # Allow ingress from other Epic 8 services
    ingress {
      from {
        namespace_selector {
          match_labels = {
            name = "epic8"
          }
        }
      }
    }

    # Allow ingress from ingress controller
    ingress {
      from {
        namespace_selector {
          match_labels = {
            name = "kube-system"
          }
        }
      }
      ports {
        protocol = "TCP"
        port     = "80"
      }
      ports {
        protocol = "TCP"
        port     = "443"
      }
    }

    # Allow egress to other Epic 8 services
    egress {
      to {
        namespace_selector {
          match_labels = {
            name = "epic8"
          }
        }
      }
    }

    # Allow egress to external services (DNS, HTTPS)
    egress {
      ports {
        protocol = "TCP"
        port     = "53"
      }
      ports {
        protocol = "UDP"
        port     = "53"
      }
      ports {
        protocol = "TCP"
        port     = "443"
      }
      ports {
        protocol = "TCP"
        port     = "80"
      }
    }
  }

  depends_on = [helm_release.epic8_platform]
}

# Azure Policy Constraints (if Azure Policy is enabled)
resource "kubernetes_manifest" "epic8_azure_policy" {
  for_each = var.deploy_epic8_platform && var.enable_azure_policy ? toset([
    "require-pod-security-standards",
    "enforce-resource-limits",
    "restrict-registry-sources"
  ]) : toset([])

  manifest = {
    apiVersion = "templates.gatekeeper.sh/v1beta1"
    kind       = "ConstraintTemplate"
    metadata = {
      name = each.key
      labels = {
        "app.kubernetes.io/managed-by" = "terraform"
        "epic8.io/component"           = "policy"
      }
    }
    spec = {
      crd = {
        spec = {
          names = {
            kind = title(replace(each.key, "-", ""))
          }
          validation = {
            openAPIV3Schema = {
              type = "object"
              properties = {
                exemptImages = {
                  type = "array"
                  items = {
                    type = "string"
                  }
                }
              }
            }
          }
        }
      }
      targets = [
        {
          target = "admission.k8s.gatekeeper.sh"
          rego = templatefile("${path.module}/policies/${each.key}.rego", {
            environment = var.environment
            swiss_compliance = var.swiss_compliance_enabled
          })
        }
      ]
    }
  }

  depends_on = [helm_release.epic8_platform]
}