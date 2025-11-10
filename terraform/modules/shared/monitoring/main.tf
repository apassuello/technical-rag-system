# Shared Monitoring Module for Multi-Cloud Epic 8 Deployment
# Swiss Engineering Standards: Unified Observability Stack

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

# Local values for monitoring configuration
locals {
  # Environment-specific monitoring configurations
  monitoring_configs = {
    dev = {
      prometheus_retention    = "7d"
      prometheus_storage     = "10Gi"
      grafana_storage       = "5Gi"
      alert_manager_storage = "2Gi"
      jaeger_storage        = "5Gi"
      log_retention_days    = 7
    }
    staging = {
      prometheus_retention    = "15d"
      prometheus_storage     = "25Gi"
      grafana_storage       = "10Gi"
      alert_manager_storage = "5Gi"
      jaeger_storage        = "10Gi"
      log_retention_days    = 15
    }
    prod = {
      prometheus_retention    = "30d"
      prometheus_storage     = "100Gi"
      grafana_storage       = "20Gi"
      alert_manager_storage = "10Gi"
      jaeger_storage        = "50Gi"
      log_retention_days    = 90
    }
  }

  current_config = local.monitoring_configs[var.environment]

  # Swiss compliance labels
  common_labels = {
    "epic8.io/component"    = "monitoring"
    "epic8.io/environment"  = var.environment
    "epic8.io/managed-by"   = "terraform"
    "epic8.io/swiss-compliance" = var.swiss_compliance_enabled ? "enabled" : "disabled"
  }
}

# Monitoring namespace
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = var.monitoring_namespace
    labels = merge(local.common_labels, {
      "name" = var.monitoring_namespace
      "epic8.io/purpose" = "observability"
    })
    annotations = var.swiss_compliance_enabled ? {
      "epic8.io/data-classification" = "internal"
      "epic8.io/data-residency"     = "eu"
    } : {}
  }
}

# Prometheus Operator
resource "helm_release" "prometheus_operator" {
  count = var.enable_prometheus ? 1 : 0

  name       = "prometheus-operator"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "57.0.3"

  values = [
    yamlencode({
      # Global configurations
      global = {
        imageRegistry = var.image_registry
      }

      # Prometheus configuration
      prometheus = {
        prometheusSpec = {
          retention = local.current_config.prometheus_retention
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = var.storage_class
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = local.current_config.prometheus_storage
                  }
                }
              }
            }
          }

          # Resource management for Swiss efficiency
          resources = {
            requests = {
              cpu    = var.environment == "prod" ? "1" : "500m"
              memory = var.environment == "prod" ? "4Gi" : "2Gi"
            }
            limits = {
              cpu    = var.environment == "prod" ? "4" : "2"
              memory = var.environment == "prod" ? "8Gi" : "4Gi"
            }
          }

          # Security and compliance
          securityContext = {
            runAsUser  = 65534
            runAsGroup = 65534
            fsGroup    = 65534
          }

          # Service monitor selector
          serviceMonitorSelectorNilUsesHelmValues = false
          serviceMonitorSelector = {
            matchLabels = {
              "epic8.io/monitor" = "true"
            }
          }

          # Rule selector
          ruleSelectorNilUsesHelmValues = false
          ruleSelector = {
            matchLabels = {
              "epic8.io/rules" = "true"
            }
          }

          # Additional scrape configs for Epic 8
          additionalScrapeConfigs = [
            {
              job_name = "epic8-services"
              kubernetes_sd_configs = [
                {
                  role = "endpoints"
                  namespaces = {
                    names = ["epic8"]
                  }
                }
              ]
              relabel_configs = [
                {
                  source_labels = ["__meta_kubernetes_service_annotation_epic8_io_metrics"]
                  action        = "keep"
                  regex         = "true"
                },
                {
                  source_labels = ["__meta_kubernetes_service_name"]
                  target_label  = "service"
                },
                {
                  source_labels = ["__meta_kubernetes_namespace"]
                  target_label  = "namespace"
                }
              ]
            }
          ]
        }

        # Ingress for Prometheus (if enabled)
        ingress = var.enable_ingress ? {
          enabled = true
          ingressClassName = var.ingress_class
          annotations = merge(var.ingress_annotations, {
            "nginx.ingress.kubernetes.io/auth-type" = "basic"
            "nginx.ingress.kubernetes.io/auth-secret" = "prometheus-auth"
          })
          hosts = [
            {
              host = "prometheus-${var.environment}.${var.domain_name}"
              paths = [
                {
                  path     = "/"
                  pathType = "Prefix"
                }
              ]
            }
          ]
          tls = var.enable_tls ? [
            {
              secretName = "prometheus-tls"
              hosts      = ["prometheus-${var.environment}.${var.domain_name}"]
            }
          ] : []
        } : { enabled = false }
      }

      # Grafana configuration
      grafana = var.enable_grafana ? {
        enabled = true

        persistence = {
          enabled      = true
          size         = local.current_config.grafana_storage
          storageClassName = var.storage_class
        }

        # Admin credentials
        adminPassword = var.grafana_admin_password

        # Resource management
        resources = {
          requests = {
            cpu    = "100m"
            memory = "256Mi"
          }
          limits = {
            cpu    = "500m"
            memory = "1Gi"
          }
        }

        # Grafana configuration
        grafana.ini = {
          server = {
            root_url = var.enable_ingress ? "https://grafana-${var.environment}.${var.domain_name}" : ""
          }
          security = {
            cookie_secure = var.enable_tls
            strict_transport_security = var.enable_tls
          }
          auth = {
            disable_login_form = false
            oauth_auto_login   = false
          }
          "auth.generic_oauth" = var.enable_oauth ? {
            enabled        = true
            name           = "Swiss OAuth"
            allow_sign_up  = true
            client_id      = var.oauth_client_id
            client_secret  = var.oauth_client_secret
            scopes         = "openid profile email"
            auth_url       = var.oauth_auth_url
            token_url      = var.oauth_token_url
            api_url        = var.oauth_api_url
          } : {}
          analytics = {
            reporting_enabled = false  # Swiss privacy compliance
            check_for_updates = false
          }
        }

        # Predefined dashboards for Epic 8
        dashboardProviders = {
          "dashboardproviders.yaml" = {
            apiVersion = 1
            providers = [
              {
                name   = "epic8"
                orgId  = 1
                folder = "Epic 8"
                type   = "file"
                disableDeletion = true
                editable = false
                options = {
                  path = "/var/lib/grafana/dashboards/epic8"
                }
              }
            ]
          }
        }

        dashboards = {
          epic8 = {
            "epic8-overview" = {
              gnetId     = 14031  # Node Exporter Full
              revision   = 2
              datasource = "Prometheus"
            }
            "epic8-services" = {
              json = file("${path.module}/dashboards/epic8-services.json")
            }
            "epic8-performance" = {
              json = file("${path.module}/dashboards/epic8-performance.json")
            }
          }
        }

        # Ingress for Grafana
        ingress = var.enable_ingress ? {
          enabled = true
          ingressClassName = var.ingress_class
          annotations = var.ingress_annotations
          hosts = [
            {
              host = "grafana-${var.environment}.${var.domain_name}"
              paths = [
                {
                  path     = "/"
                  pathType = "Prefix"
                }
              ]
            }
          ]
          tls = var.enable_tls ? [
            {
              secretName = "grafana-tls"
              hosts      = ["grafana-${var.environment}.${var.domain_name}"]
            }
          ] : []
        } : { enabled = false }
      } : { enabled = false }

      # AlertManager configuration
      alertmanager = var.enable_alertmanager ? {
        alertmanagerSpec = {
          storage = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = var.storage_class
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = local.current_config.alert_manager_storage
                  }
                }
              }
            }
          }

          # Resource management
          resources = {
            requests = {
              cpu    = "100m"
              memory = "256Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "1Gi"
            }
          }

          # AlertManager configuration
          configSecret = "alertmanager-config"
        }

        # Ingress for AlertManager
        ingress = var.enable_ingress ? {
          enabled = true
          ingressClassName = var.ingress_class
          annotations = merge(var.ingress_annotations, {
            "nginx.ingress.kubernetes.io/auth-type" = "basic"
            "nginx.ingress.kubernetes.io/auth-secret" = "alertmanager-auth"
          })
          hosts = [
            {
              host = "alertmanager-${var.environment}.${var.domain_name}"
              paths = [
                {
                  path     = "/"
                  pathType = "Prefix"
                }
              ]
            }
          ]
          tls = var.enable_tls ? [
            {
              secretName = "alertmanager-tls"
              hosts      = ["alertmanager-${var.environment}.${var.domain_name}"]
            }
          ] : []
        } : { enabled = false }
      } : { enabled = false }

      # Node Exporter
      nodeExporter = {
        enabled = var.enable_node_exporter
      }

      # kube-state-metrics
      kubeStateMetrics = {
        enabled = true
      }

      # Default service monitors
      defaultRules = {
        create = true
        rules = {
          etcd                 = false  # Not available in managed Kubernetes
          kubernetesApps      = true
          kubernetesResources = true
          kubernetesStorage   = true
          kubernetesSystem    = true
          node                = var.enable_node_exporter
          prometheus          = true
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# Jaeger for distributed tracing
resource "helm_release" "jaeger" {
  count = var.enable_jaeger ? 1 : 0

  name       = "jaeger"
  repository = "https://jaegertracing.github.io/helm-charts"
  chart      = "jaeger"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "0.71.14"

  values = [
    yamlencode({
      provisionDataStore = {
        cassandra = false
        elasticsearch = var.environment == "prod"
        kafka = false
      }

      storage = {
        type = var.environment == "prod" ? "elasticsearch" : "memory"

        # Elasticsearch configuration for production
        elasticsearch = var.environment == "prod" ? {
          host = "elasticsearch.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local"
          port = 9200
        } : {}
      }

      agent = {
        enabled = true
        daemonset = {
          useHostPort = true
        }
      }

      collector = {
        enabled = true
        replicaCount = var.environment == "prod" ? 3 : 1

        resources = {
          requests = {
            cpu    = "100m"
            memory = "256Mi"
          }
          limits = {
            cpu    = var.environment == "prod" ? "1" : "500m"
            memory = var.environment == "prod" ? "2Gi" : "1Gi"
          }
        }

        service = {
          type = "ClusterIP"
          annotations = {
            "epic8.io/monitor" = "true"
          }
        }
      }

      query = {
        enabled = true
        replicaCount = var.environment == "prod" ? 2 : 1

        resources = {
          requests = {
            cpu    = "100m"
            memory = "256Mi"
          }
          limits = {
            cpu    = "500m"
            memory = "1Gi"
          }
        }

        # Ingress for Jaeger UI
        ingress = var.enable_ingress ? {
          enabled = true
          ingressClassName = var.ingress_class
          annotations = var.ingress_annotations
          hosts = [
            {
              host = "jaeger-${var.environment}.${var.domain_name}"
              paths = [
                {
                  path     = "/"
                  pathType = "Prefix"
                }
              ]
            }
          ]
          tls = var.enable_tls ? [
            {
              secretName = "jaeger-tls"
              hosts      = ["jaeger-${var.environment}.${var.domain_name}"]
            }
          ] : []
        } : { enabled = false }
      }
    })
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# OpenTelemetry Collector for Epic 8 telemetry
resource "helm_release" "opentelemetry_collector" {
  count = var.enable_opentelemetry ? 1 : 0

  name       = "opentelemetry-collector"
  repository = "https://open-telemetry.github.io/opentelemetry-helm-charts"
  chart      = "opentelemetry-collector"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "0.69.0"

  values = [
    yamlencode({
      mode = "deployment"

      config = {
        receivers = {
          otlp = {
            protocols = {
              grpc = {
                endpoint = "0.0.0.0:4317"
              }
              http = {
                endpoint = "0.0.0.0:4318"
              }
            }
          }
          prometheus = {
            config = {
              scrape_configs = [
                {
                  job_name = "epic8-otel-collector"
                  scrape_interval = "10s"
                  static_configs = [
                    {
                      targets = ["0.0.0.0:8888"]
                    }
                  ]
                }
              ]
            }
          }
        }

        processors = {
          batch = {}
          memory_limiter = {
            limit_mib = 512
          }
          attributes = {
            actions = [
              {
                key    = "epic8.environment"
                value  = var.environment
                action = "insert"
              },
              {
                key    = "epic8.cluster"
                value  = var.cluster_name
                action = "insert"
              }
            ]
          }
        }

        exporters = merge(
          var.enable_prometheus ? {
            prometheus = {
              endpoint = "0.0.0.0:8889"
              const_labels = {
                environment = var.environment
                cluster     = var.cluster_name
              }
            }
          } : {},
          var.enable_jaeger ? {
            jaeger = {
              endpoint = "jaeger-collector.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local:14250"
              tls = {
                insecure = true
              }
            }
          } : {}
        )

        service = {
          pipelines = {
            traces = {
              receivers  = ["otlp"]
              processors = ["memory_limiter", "batch", "attributes"]
              exporters  = var.enable_jaeger ? ["jaeger"] : []
            }
            metrics = {
              receivers  = ["otlp", "prometheus"]
              processors = ["memory_limiter", "batch", "attributes"]
              exporters  = var.enable_prometheus ? ["prometheus"] : []
            }
          }
        }
      }

      resources = {
        requests = {
          cpu    = "100m"
          memory = "256Mi"
        }
        limits = {
          cpu    = "500m"
          memory = "1Gi"
        }
      }

      service = {
        annotations = {
          "epic8.io/monitor" = "true"
        }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace.monitoring,
    helm_release.prometheus_operator,
    helm_release.jaeger
  ]
}