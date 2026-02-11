# GKE Add-ons and Essential Services Configuration
# Swiss Engineering Standards: Automated Deployment, Monitoring, Security

# Configure Kubernetes and Helm providers for GKE
data "google_client_config" "provider" {}

provider "kubernetes" {
  host  = "https://${google_container_cluster.primary.endpoint}"
  token = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(
    google_container_cluster.primary.master_auth[0].cluster_ca_certificate,
  )
}

provider "helm" {
  kubernetes {
    host  = "https://${google_container_cluster.primary.endpoint}"
    token = data.google_client_config.provider.access_token
    cluster_ca_certificate = base64decode(
      google_container_cluster.primary.master_auth[0].cluster_ca_certificate,
    )
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

  # Environment-specific values for GKE
  values = var.epic8_values_file != "" ? [
    file(var.epic8_values_file)
  ] : [
    yamlencode({
      global = {
        environment     = var.environment
        clusterName     = google_container_cluster.primary.name
        region          = var.region
        provider        = "gcp"
        swissCompliance = var.swiss_compliance_enabled
        projectId       = var.project_id
      }

      # Service configurations optimized for GKE and Swiss performance standards
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
            "epic8.io/node-type" = "general"
          }
        }

        queryAnalyzer = {
          replicaCount = var.environment == "prod" ? 2 : 1
          nodeSelector = {
            "epic8.io/node-type" = "ml-workloads"
          }
          tolerations = [{
            key      = "workload.epic8.io/ml"
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
            "epic8.io/node-type" = "general"
          }
        }

        generator = {
          replicaCount = var.environment == "prod" ? 2 : 1
          nodeSelector = {
            "epic8.io/node-type" = "ml-workloads"
          }
          tolerations = [{
            key      = "workload.epic8.io/ml"
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
              "epic8.io/node-type" = "general"
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
              "epic8.io/node-type" = "general"
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
              "epic8.io/node-type" = "general"
            }
          }
        }
      }

      # Ingress configuration for GKE with Swiss accessibility
      ingress = {
        enabled     = true
        className   = "gce"
        annotations = {
          "kubernetes.io/ingress.class"                = "gce"
          "kubernetes.io/ingress.global-static-ip-name" = google_compute_global_address.epic8_ip[0].name
          "ingress.gcp.kubernetes.io/managed-certificates" = google_compute_managed_ssl_certificate.epic8_ssl[0].name
          "cloud.google.com/armor-config"             = "{\"${google_compute_security_policy.epic8_security_policy[0].name}\": \"epic8-security-policy\"}"
          "cloud.google.com/backend-config"           = "{\"default\": \"epic8-backend-config\"}"
        }
        hosts = [
          {
            host = var.environment == "prod" ? "epic8.yourdomain.com" : "${var.environment}-epic8.yourdomain.com"
            paths = [
              {
                path     = "/*"
                pathType = "ImplementationSpecific"
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

      # Security and compliance configurations for GKE
      security = {
        networkPolicies = {
          enabled = var.enable_network_policy
        }
        podSecurityStandards = {
          enabled = var.security_level != "basic"
          level   = var.security_level == "maximum" ? "restricted" : "baseline"
        }
        serviceMonitor = {
          enabled = var.enable_monitoring
        }
        workloadIdentity = {
          enabled   = var.enable_workload_identity
          projectId = var.project_id
        }
      }

      # GKE-specific configurations
      gke = {
        workloadIdentity = {
          enabled = var.enable_workload_identity
        }
        nodeSelector = {
          "epic8.io/node-type" = "general"
        }
      }
    })
  ]

  depends_on = [
    google_container_node_pool.pools,
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

  depends_on = [google_container_cluster.primary]
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

  storage_provisioner    = "kubernetes.io/gce-pd"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    type             = "pd-ssd"
    zones            = join(",", data.google_compute_zones.available.names)
    replication-type = var.environment == "prod" ? "regional-pd" : "none"
  }

  depends_on = [google_container_cluster.primary]
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

  storage_provisioner    = "kubernetes.io/gce-pd"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    type             = "pd-standard"
    zones            = join(",", data.google_compute_zones.available.names)
    replication-type = var.environment == "prod" ? "regional-pd" : "none"
  }

  depends_on = [google_container_cluster.primary]
}

# Global IP address for Epic 8 platform
resource "google_compute_global_address" "epic8_ip" {
  count = var.deploy_epic8_platform ? 1 : 0

  name         = "${local.cluster_name}-epic8-ip"
  address_type = "EXTERNAL"
  ip_version   = "IPV4"

  labels = merge(local.common_labels, {
    component = "networking"
    purpose   = "epic8-ingress"
  })
}

# Managed SSL certificate for Epic 8 platform
resource "google_compute_managed_ssl_certificate" "epic8_ssl" {
  count = var.deploy_epic8_platform ? 1 : 0

  name = "${local.cluster_name}-epic8-ssl"

  managed {
    domains = [
      var.environment == "prod" ? "epic8.yourdomain.com" : "${var.environment}-epic8.yourdomain.com"
    ]
  }

  labels = merge(local.common_labels, {
    component = "security"
    purpose   = "ssl-certificate"
  })
}

# Cloud Armor security policy for Epic 8
resource "google_compute_security_policy" "epic8_security_policy" {
  count = var.deploy_epic8_platform && var.security_level != "basic" ? 1 : 0

  name        = "${local.cluster_name}-epic8-security-policy"
  description = "Cloud Armor security policy for Epic 8 RAG platform"

  # Default rule
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }

  # Block common attack patterns
  rule {
    action   = "deny(403)"
    priority = "1000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-stable')"
      }
    }
    description = "Deny SQL injection attacks"
  }

  rule {
    action   = "deny(403)"
    priority = "1001"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-stable')"
      }
    }
    description = "Deny XSS attacks"
  }

  # Rate limiting for Swiss compliance
  rule {
    action   = "rate_based_ban"
    priority = "1002"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Rate limiting rule"
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
      ban_duration_sec = 300
    }
  }

  # Geographic restrictions (maximum security)
  dynamic "rule" {
    for_each = var.security_level == "maximum" ? [1] : []
    content {
      action   = "deny(403)"
      priority = "1003"
      match {
        expr {
          expression = "origin.region_code != 'CH' && origin.region_code != 'DE' && origin.region_code != 'AT' && origin.region_code != 'FR' && origin.region_code != 'IT'"
        }
      }
      description = "Allow only DACH region and neighbors"
    }
  }

  labels = merge(local.common_labels, {
    component = "security"
    purpose   = "waf-protection"
  })
}

# Backend configuration for Epic 8 services
resource "kubernetes_config_map" "epic8_backend_config" {
  count = var.deploy_epic8_platform ? 1 : 0

  metadata {
    name      = "epic8-backend-config"
    namespace = "epic8"
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "epic8.io/component"           = "configuration"
    }
  }

  data = {
    "backend-config.yaml" = yamlencode({
      apiVersion = "cloud.google.com/v1"
      kind       = "BackendConfig"
      metadata = {
        name      = "epic8-backend-config"
        namespace = "epic8"
      }
      spec = {
        healthCheck = {
          checkIntervalSec   = 10
          timeoutSec        = 5
          healthyThreshold  = 1
          unhealthyThreshold = 3
          type              = "HTTP"
          requestPath       = "/health"
          port              = 8080
        }
        sessionAffinity = {
          affinityType         = "CLIENT_IP"
          affinityCookieTtlSec = 3600
        }
        timeoutSec = 30
        connectionDraining = {
          drainingTimeoutSec = 60
        }
        logging = {
          enable     = var.environment == "prod"
          sampleRate = var.environment == "prod" ? 0.1 : 1.0
        }
        securityPolicy = var.security_level != "basic" ? {
          name = google_compute_security_policy.epic8_security_policy[0].name
        } : null
      }
    })
  }

  depends_on = [helm_release.epic8_platform]
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

# Network policies for Epic 8 services (if network policy is enabled)
resource "kubernetes_network_policy" "epic8_network_policies" {
  for_each = var.deploy_epic8_platform && var.enable_network_policy ? toset([
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

    # Allow egress to other Epic 8 services and external APIs
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