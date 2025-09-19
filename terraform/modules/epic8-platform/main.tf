# Epic 8 Platform Deployment Module
# Swiss Engineering Standards: Production-Ready RAG Platform Deployment

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
}

# Local values for Epic 8 platform configuration
locals {
  # Environment-specific platform configurations
  platform_configs = {
    dev = {
      api_gateway_replicas    = 1
      query_analyzer_replicas = 1
      retriever_replicas     = 1
      generator_replicas     = 1
      cache_replicas         = 1
      analytics_replicas     = 1
      enable_hpa            = false
      enable_pdb            = false
      resource_requests = {
        cpu    = "100m"
        memory = "256Mi"
      }
      resource_limits = {
        cpu    = "500m"
        memory = "1Gi"
      }
    }
    staging = {
      api_gateway_replicas    = 2
      query_analyzer_replicas = 2
      retriever_replicas     = 2
      generator_replicas     = 2
      cache_replicas         = 2
      analytics_replicas     = 1
      enable_hpa            = true
      enable_pdb            = true
      resource_requests = {
        cpu    = "200m"
        memory = "512Mi"
      }
      resource_limits = {
        cpu    = "1"
        memory = "2Gi"
      }
    }
    prod = {
      api_gateway_replicas    = 3
      query_analyzer_replicas = 3
      retriever_replicas     = 3
      generator_replicas     = 3
      cache_replicas         = 3
      analytics_replicas     = 2
      enable_hpa            = true
      enable_pdb            = true
      resource_requests = {
        cpu    = "500m"
        memory = "1Gi"
      }
      resource_limits = {
        cpu    = "2"
        memory = "4Gi"
      }
    }
  }

  current_config = local.platform_configs[var.environment]

  # Swiss compliance and platform labels
  common_labels = {
    "app.kubernetes.io/part-of"     = "epic8-platform"
    "app.kubernetes.io/managed-by"  = "terraform"
    "epic8.io/environment"          = var.environment
    "epic8.io/swiss-compliance"     = var.swiss_compliance_enabled ? "enabled" : "disabled"
    "epic8.io/version"              = var.platform_version
  }
}

# Epic 8 namespace
resource "kubernetes_namespace" "epic8" {
  metadata {
    name = var.epic8_namespace
    labels = merge(local.common_labels, {
      "name" = var.epic8_namespace
      "epic8.io/purpose" = "rag-platform"
      "pod-security.kubernetes.io/enforce" = var.pod_security_standard
      "pod-security.kubernetes.io/audit"   = var.pod_security_standard
      "pod-security.kubernetes.io/warn"    = var.pod_security_standard
    })
    annotations = var.swiss_compliance_enabled ? {
      "epic8.io/data-classification" = "internal"
      "epic8.io/data-residency"     = "eu"
      "epic8.io/compliance-framework" = "gdpr"
    } : {}
  }
}

# ConfigMap for platform configuration
resource "kubernetes_config_map" "epic8_config" {
  metadata {
    name      = "epic8-config"
    namespace = kubernetes_namespace.epic8.metadata[0].name
    labels    = merge(local.common_labels, {
      "epic8.io/component" = "configuration"
    })
  }

  data = {
    # Platform configuration
    "platform.yaml" = yamlencode({
      platform = {
        name        = "epic8-rag"
        version     = var.platform_version
        environment = var.environment
        region      = var.region
        cloud       = var.cloud_provider
      }

      # Service discovery
      services = {
        api_gateway = {
          host = "api-gateway.${kubernetes_namespace.epic8.metadata[0].name}.svc.cluster.local"
          port = 8080
        }
        query_analyzer = {
          host = "query-analyzer.${kubernetes_namespace.epic8.metadata[0].name}.svc.cluster.local"
          port = 8081
        }
        retriever = {
          host = "retriever.${kubernetes_namespace.epic8.metadata[0].name}.svc.cluster.local"
          port = 8082
        }
        generator = {
          host = "generator.${kubernetes_namespace.epic8.metadata[0].name}.svc.cluster.local"
          port = 8083
        }
        cache = {
          host = "cache.${kubernetes_namespace.epic8.metadata[0].name}.svc.cluster.local"
          port = 6379
        }
        analytics = {
          host = "analytics.${kubernetes_namespace.epic8.metadata[0].name}.svc.cluster.local"
          port = 8085
        }
      }

      # Database configuration
      database = {
        host     = var.database_host
        port     = var.database_port
        name     = var.database_name
        ssl_mode = "require"
      }

      # Cache configuration
      cache = {
        redis = {
          host = "redis.${kubernetes_namespace.epic8.metadata[0].name}.svc.cluster.local"
          port = 6379
          db   = 0
        }
      }

      # Monitoring configuration
      monitoring = {
        prometheus = {
          enabled = var.enable_monitoring
          port    = 9090
        }
        jaeger = {
          enabled  = var.enable_tracing
          endpoint = var.jaeger_endpoint
        }
        logging = {
          level  = var.log_level
          format = "json"
        }
      }

      # Swiss compliance settings
      compliance = var.swiss_compliance_enabled ? {
        gdpr = {
          enabled            = true
          data_retention_days = var.data_retention_days
          anonymization      = true
        }
        encryption = {
          at_rest     = true
          in_transit  = true
          algorithm   = "AES-256-GCM"
        }
      } : {}
    })

    # Feature flags
    "features.yaml" = yamlencode({
      features = {
        multi_model_routing     = var.enable_multi_model_routing
        cost_optimization      = var.enable_cost_optimization
        query_caching         = var.enable_query_caching
        result_caching        = var.enable_result_caching
        auto_scaling          = local.current_config.enable_hpa
        distributed_tracing   = var.enable_tracing
        metrics_collection    = var.enable_monitoring
        rate_limiting         = var.enable_rate_limiting
        circuit_breaker       = var.enable_circuit_breaker
        health_checks         = true
        graceful_shutdown     = true
      }
    })
  }
}

# Secrets for Epic 8 platform
resource "kubernetes_secret" "epic8_secrets" {
  metadata {
    name      = "epic8-secrets"
    namespace = kubernetes_namespace.epic8.metadata[0].name
    labels    = merge(local.common_labels, {
      "epic8.io/component" = "secrets"
    })
  }

  type = "Opaque"

  data = {
    # Database credentials
    database_username = base64encode(var.database_username)
    database_password = base64encode(var.database_password)

    # API keys for external services
    openai_api_key     = base64encode(var.openai_api_key)
    anthropic_api_key  = base64encode(var.anthropic_api_key)
    mistral_api_key    = base64encode(var.mistral_api_key)

    # JWT secrets
    jwt_secret = base64encode(var.jwt_secret)

    # Encryption keys
    encryption_key = base64encode(var.encryption_key)

    # Additional secrets
    for secret_name, secret_value in var.additional_secrets : secret_name => base64encode(secret_value)
  }
}

# API Gateway Deployment
resource "kubernetes_deployment" "api_gateway" {
  metadata {
    name      = "api-gateway"
    namespace = kubernetes_namespace.epic8.metadata[0].name
    labels    = merge(local.common_labels, {
      "app.kubernetes.io/name"      = "api-gateway"
      "app.kubernetes.io/component" = "gateway"
      "epic8.io/service"           = "api-gateway"
    })
  }

  spec {
    replicas = local.current_config.api_gateway_replicas

    selector {
      match_labels = {
        "app.kubernetes.io/name" = "api-gateway"
      }
    }

    template {
      metadata {
        labels = merge(local.common_labels, {
          "app.kubernetes.io/name" = "api-gateway"
          "epic8.io/service"      = "api-gateway"
        })
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "8080"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        service_account_name = var.enable_rbac ? kubernetes_service_account.epic8_services["api-gateway"].metadata[0].name : "default"

        container {
          name  = "api-gateway"
          image = "${var.image_registry}/${var.api_gateway_image}:${var.platform_version}"

          port {
            name           = "http"
            container_port = 8080
            protocol       = "TCP"
          }

          port {
            name           = "metrics"
            container_port = 9090
            protocol       = "TCP"
          }

          env {
            name = "ENVIRONMENT"
            value = var.environment
          }

          env {
            name = "LOG_LEVEL"
            value = var.log_level
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.epic8_config.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.epic8_secrets.metadata[0].name
            }
          }

          resources {
            requests = {
              cpu    = local.current_config.resource_requests.cpu
              memory = local.current_config.resource_requests.memory
            }
            limits = {
              cpu    = local.current_config.resource_limits.cpu
              memory = local.current_config.resource_limits.memory
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8080
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/ready"
              port = 8080
            }
            initial_delay_seconds = 10
            period_seconds        = 5
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          # Security context for Swiss compliance
          security_context {
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            run_as_non_root           = true
            run_as_user               = 1001
            run_as_group              = 1001
            capabilities {
              drop = ["ALL"]
            }
          }

          volume_mount {
            name       = "tmp"
            mount_path = "/tmp"
          }

          volume_mount {
            name       = "cache"
            mount_path = "/app/cache"
          }
        }

        volume {
          name = "tmp"
          empty_dir {}
        }

        volume {
          name = "cache"
          empty_dir {}
        }

        # Pod security context
        security_context {
          run_as_non_root = true
          run_as_user     = 1001
          run_as_group    = 1001
          fs_group        = 1001
        }

        # Node selection
        node_selector = var.node_selector

        # Tolerations
        dynamic "toleration" {
          for_each = var.tolerations
          content {
            key      = toleration.value.key
            operator = toleration.value.operator
            value    = toleration.value.value
            effect   = toleration.value.effect
          }
        }

        # Anti-affinity for high availability
        affinity {
          pod_anti_affinity {
            preferred_during_scheduling_ignored_during_execution {
              weight = 100
              pod_affinity_term {
                label_selector {
                  match_expressions {
                    key      = "app.kubernetes.io/name"
                    operator = "In"
                    values   = ["api-gateway"]
                  }
                }
                topology_key = "kubernetes.io/hostname"
              }
            }
          }
        }
      }
    }

    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_unavailable = "25%"
        max_surge       = "25%"
      }
    }
  }
}

# API Gateway Service
resource "kubernetes_service" "api_gateway" {
  metadata {
    name      = "api-gateway"
    namespace = kubernetes_namespace.epic8.metadata[0].name
    labels    = merge(local.common_labels, {
      "app.kubernetes.io/name" = "api-gateway"
      "epic8.io/service"      = "api-gateway"
    })
    annotations = {
      "prometheus.io/scrape" = "true"
      "prometheus.io/port"   = "8080"
      "epic8.io/monitor"     = "true"
    }
  }

  spec {
    selector = {
      "app.kubernetes.io/name" = "api-gateway"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 8080
      protocol    = "TCP"
    }

    port {
      name        = "metrics"
      port        = 9090
      target_port = 9090
      protocol    = "TCP"
    }

    type = "ClusterIP"
  }
}

# Similar deployments and services for other Epic 8 components would follow the same pattern
# For brevity, I'll include the key components with the same comprehensive configuration

# Horizontal Pod Autoscaler for API Gateway
resource "kubernetes_horizontal_pod_autoscaler_v2" "api_gateway" {
  count = local.current_config.enable_hpa ? 1 : 0

  metadata {
    name      = "api-gateway-hpa"
    namespace = kubernetes_namespace.epic8.metadata[0].name
    labels    = local.common_labels
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.api_gateway.metadata[0].name
    }

    min_replicas = local.current_config.api_gateway_replicas
    max_replicas = local.current_config.api_gateway_replicas * 3

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type               = "Utilization"
          average_utilization = 70
        }
      }
    }

    metric {
      type = "Resource"
      resource {
        name = "memory"
        target {
          type               = "Utilization"
          average_utilization = 80
        }
      }
    }

    behavior {
      scale_up {
        stabilization_window_seconds = 60
        policy {
          type          = "Percent"
          value         = 50
          period_seconds = 60
        }
      }
      scale_down {
        stabilization_window_seconds = 300
        policy {
          type          = "Percent"
          value         = 25
          period_seconds = 60
        }
      }
    }
  }
}

# Pod Disruption Budget
resource "kubernetes_pod_disruption_budget_v1" "api_gateway" {
  count = local.current_config.enable_pdb ? 1 : 0

  metadata {
    name      = "api-gateway-pdb"
    namespace = kubernetes_namespace.epic8.metadata[0].name
    labels    = local.common_labels
  }

  spec {
    min_available = "50%"
    selector {
      match_labels = {
        "app.kubernetes.io/name" = "api-gateway"
      }
    }
  }
}

# Service Accounts for RBAC
resource "kubernetes_service_account" "epic8_services" {
  for_each = var.enable_rbac ? toset([
    "api-gateway",
    "query-analyzer",
    "retriever",
    "generator",
    "cache",
    "analytics"
  ]) : toset([])

  metadata {
    name      = "${each.key}-sa"
    namespace = kubernetes_namespace.epic8.metadata[0].name
    labels    = merge(local.common_labels, {
      "epic8.io/service" = each.key
    })
    annotations = var.enable_workload_identity ? merge(
      var.cloud_provider == "aws" ? {
        "eks.amazonaws.com/role-arn" = var.workload_identity_role_arns[each.key]
      } : {},
      var.cloud_provider == "gcp" ? {
        "iam.gke.io/gcp-service-account" = var.workload_identity_service_accounts[each.key]
      } : {},
      var.cloud_provider == "azure" ? {
        "azure.workload.identity/client-id" = var.workload_identity_client_ids[each.key]
      } : {}
    ) : {}
  }
}

# Ingress for Epic 8 platform
resource "kubernetes_ingress_v1" "epic8" {
  count = var.enable_ingress ? 1 : 0

  metadata {
    name      = "epic8-ingress"
    namespace = kubernetes_namespace.epic8.metadata[0].name
    labels    = local.common_labels
    annotations = merge(
      var.ingress_annotations,
      var.enable_tls ? {
        "cert-manager.io/cluster-issuer" = var.cert_manager_issuer
      } : {}
    )
  }

  spec {
    ingress_class_name = var.ingress_class_name

    dynamic "tls" {
      for_each = var.enable_tls ? [1] : []
      content {
        hosts       = var.ingress_hosts
        secret_name = "epic8-tls"
      }
    }

    dynamic "rule" {
      for_each = var.ingress_hosts
      content {
        host = rule.value
        http {
          path {
            path      = "/"
            path_type = "Prefix"
            backend {
              service {
                name = kubernetes_service.api_gateway.metadata[0].name
                port {
                  number = 80
                }
              }
            }
          }
        }
      }
    }
  }
}