# Shared Networking Module for Multi-Cloud Epic 8 Deployment
# Swiss Engineering Standards: Efficient, Secure, Scalable Networking

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

# Local values for networking configuration
locals {
  # Environment-specific networking configurations
  networking_configs = {
    dev = {
      ingress_replicas     = 1
      load_balancer_type   = "nlb"
      enable_ssl_redirect  = false
      rate_limit_rps      = 100
      connection_timeout  = 30
    }
    staging = {
      ingress_replicas     = 2
      load_balancer_type   = "nlb"
      enable_ssl_redirect  = true
      rate_limit_rps      = 500
      connection_timeout  = 60
    }
    prod = {
      ingress_replicas     = 3
      load_balancer_type   = "nlb"
      enable_ssl_redirect  = true
      rate_limit_rps      = 1000
      connection_timeout  = 120
    }
  }

  current_config = local.networking_configs[var.environment]

  # Swiss compliance and networking labels
  common_labels = {
    "epic8.io/component"        = "networking"
    "epic8.io/environment"      = var.environment
    "epic8.io/managed-by"       = "terraform"
    "epic8.io/swiss-compliance" = var.swiss_compliance_enabled ? "enabled" : "disabled"
  }
}

# Networking namespace
resource "kubernetes_namespace" "networking" {
  metadata {
    name = var.networking_namespace
    labels = merge(local.common_labels, {
      "name" = var.networking_namespace
      "epic8.io/purpose" = "networking"
    })
    annotations = var.swiss_compliance_enabled ? {
      "epic8.io/data-classification" = "internal"
      "epic8.io/data-residency"     = "eu"
    } : {}
  }
}

# NGINX Ingress Controller
resource "helm_release" "nginx_ingress" {
  count = var.enable_nginx_ingress ? 1 : 0

  name       = "nginx-ingress"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  namespace  = var.networking_namespace
  version    = "4.8.3"

  values = [
    yamlencode({
      controller = {
        name = "nginx-ingress-controller"

        # Replica configuration based on environment
        replicaCount = local.current_config.ingress_replicas

        # Resource management for Swiss efficiency
        resources = {
          requests = {
            cpu    = var.environment == "prod" ? "200m" : "100m"
            memory = var.environment == "prod" ? "512Mi" : "256Mi"
          }
          limits = {
            cpu    = var.environment == "prod" ? "1" : "500m"
            memory = var.environment == "prod" ? "1Gi" : "512Mi"
          }
        }

        # Service configuration
        service = {
          type = var.cloud_provider == "aws" ? "LoadBalancer" : "LoadBalancer"
          annotations = merge(
            var.cloud_provider == "aws" ? {
              "service.beta.kubernetes.io/aws-load-balancer-type"                     = "nlb"
              "service.beta.kubernetes.io/aws-load-balancer-backend-protocol"        = "tcp"
              "service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled" = "true"
              "service.beta.kubernetes.io/aws-load-balancer-nlb-target-type"         = "ip"
            } : {},
            var.cloud_provider == "gcp" ? {
              "cloud.google.com/load-balancer-type" = "External"
              "cloud.google.com/neg"                = "{\"ingress\": true}"
            } : {},
            var.cloud_provider == "azure" ? {
              "service.beta.kubernetes.io/azure-load-balancer-resource-group" = var.azure_resource_group
            } : {},
            var.service_annotations
          )
          loadBalancerSourceRanges = var.allowed_cidr_blocks
        }

        # Configuration for Epic 8 optimizations
        config = {
          # Performance tuning
          "worker-processes"                = "auto"
          "worker-cpu-affinity"            = "auto"
          "worker-connections"             = "16384"
          "max-worker-open-files"          = "65536"
          "keepalive-requests"             = "100"
          "upstream-keepalive-connections" = "50"

          # SSL/TLS configuration
          "ssl-redirect"                   = local.current_config.enable_ssl_redirect ? "true" : "false"
          "ssl-protocols"                  = "TLSv1.2 TLSv1.3"
          "ssl-ciphers"                   = "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
          "ssl-prefer-server-ciphers"     = "true"
          "ssl-session-cache"             = "shared:SSL:10m"
          "ssl-session-timeout"           = "10m"

          # Security headers for Swiss compliance
          "add-headers"                    = "epic8-security/security-headers"
          "hide-headers"                   = "Server,X-Powered-By"
          "server-tokens"                  = "false"

          # Rate limiting
          "rate-limit-rps"                = tostring(local.current_config.rate_limit_rps)
          "rate-limit-connections"        = "100"

          # Timeouts
          "proxy-connect-timeout"         = tostring(local.current_config.connection_timeout)
          "proxy-send-timeout"           = "60"
          "proxy-read-timeout"           = "60"
          "proxy-next-upstream-timeout"  = "10"

          # Body size limits
          "proxy-body-size"              = "100m"
          "client-body-buffer-size"      = "1m"

          # Epic 8 specific configurations
          "enable-real-ip"               = "true"
          "use-forwarded-headers"        = "true"
          "compute-full-forwarded-for"   = "true"
          "use-proxy-protocol"           = var.enable_proxy_protocol ? "true" : "false"

          # Monitoring
          "enable-metrics"               = "true"
          "enable-opentracing"          = var.enable_tracing ? "true" : "false"
        }

        # Metrics configuration
        metrics = {
          enabled = var.enable_metrics
          service = {
            annotations = {
              "prometheus.io/scrape" = "true"
              "prometheus.io/port"   = "10254"
              "epic8.io/monitor"     = "true"
            }
          }
          serviceMonitor = {
            enabled = var.enable_metrics
            namespace = var.monitoring_namespace
            labels = {
              "epic8.io/monitor" = "true"
            }
          }
        }

        # Admission webhooks for validation
        admissionWebhooks = {
          enabled = var.enable_admission_webhooks
          annotations = {
            "epic8.io/component" = "admission-webhook"
          }
        }

        # Node selection for Epic 8
        nodeSelector = var.node_selector
        tolerations  = var.tolerations
        affinity = {
          podAntiAffinity = {
            preferredDuringSchedulingIgnoredDuringExecution = [
              {
                weight = 100
                podAffinityTerm = {
                  labelSelector = {
                    matchExpressions = [
                      {
                        key      = "app.kubernetes.io/name"
                        operator = "In"
                        values   = ["ingress-nginx"]
                      }
                    ]
                  }
                  topologyKey = "kubernetes.io/hostname"
                }
              }
            ]
          }
        }

        # Security context
        securityContext = {
          runAsNonRoot = true
          runAsUser    = 101
          runAsGroup   = 82
          capabilities = {
            drop = ["ALL"]
            add  = ["NET_BIND_SERVICE"]
          }
        }

        # Autoscaling
        autoscaling = {
          enabled     = var.enable_autoscaling
          minReplicas = local.current_config.ingress_replicas
          maxReplicas = local.current_config.ingress_replicas * 3
          targetCPUUtilizationPercentage = 70
          targetMemoryUtilizationPercentage = 80
        }
      }

      # Default backend for health checks
      defaultBackend = {
        enabled = true
        name    = "default-backend"
        image = {
          repository = "registry.k8s.io/defaultbackend-amd64"
          tag        = "1.5"
        }
        resources = {
          requests = {
            cpu    = "10m"
            memory = "20Mi"
          }
          limits = {
            cpu    = "20m"
            memory = "40Mi"
          }
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.networking]
}

# Security headers ConfigMap
resource "kubernetes_config_map" "security_headers" {
  count = var.enable_nginx_ingress ? 1 : 0

  metadata {
    name      = "security-headers"
    namespace = var.networking_namespace
    labels    = local.common_labels
  }

  data = {
    "X-Frame-Options"           = "DENY"
    "X-Content-Type-Options"    = "nosniff"
    "X-XSS-Protection"         = "1; mode=block"
    "Strict-Transport-Security" = "max-age=31536000; includeSubDomains; preload"
    "Content-Security-Policy"   = var.content_security_policy
    "Referrer-Policy"          = "strict-origin-when-cross-origin"
    "Permissions-Policy"       = "geolocation=(), microphone=(), camera=()"
  }
}

# Istio Service Mesh (if enabled)
resource "helm_release" "istio_base" {
  count = var.enable_istio ? 1 : 0

  name       = "istio-base"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "base"
  namespace  = "istio-system"
  version    = "1.19.3"

  create_namespace = true

  values = [
    yamlencode({
      global = {
        meshID      = var.mesh_id
        network     = var.network_name
        hub         = var.istio_hub
        tag         = var.istio_version

        # Swiss compliance settings
        tracer = {
          zipkin = {
            address = var.enable_tracing ? "${var.jaeger_endpoint}:9411" : ""
          }
        }
      }
    })
  ]
}

resource "helm_release" "istiod" {
  count = var.enable_istio ? 1 : 0

  name       = "istiod"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  namespace  = "istio-system"
  version    = "1.19.3"

  values = [
    yamlencode({
      pilot = {
        resources = {
          requests = {
            cpu    = "100m"
            memory = "128Mi"
          }
          limits = {
            cpu    = var.environment == "prod" ? "1" : "500m"
            memory = var.environment == "prod" ? "2Gi" : "1Gi"
          }
        }

        # Environment configuration
        env = {
          PILOT_TRACE_SAMPLING = var.enable_tracing ? 1.0 : 0.0
          PILOT_ENABLE_WORKLOAD_ENTRY_AUTOREGISTRATION = true
        }

        # Security settings
        seccompProfile = {
          type = "RuntimeDefault"
        }
      }

      global = {
        meshID  = var.mesh_id
        network = var.network_name

        # Telemetry configuration
        defaultConfig = {
          discoveryRefreshDelay = "10s"
          proxyStatsMatcher = {
            inclusionRegexps = [
              ".*circuit_breakers.*",
              ".*upstream_rq_retry.*",
              ".*upstream_rq_pending.*"
            ]
          }
        }
      }

      # Telemetry v2 configuration
      telemetry = {
        v2 = {
          enabled = true
          prometheus = {
            configOverride = {
              disable_host_header_fallback = true
            }
          }
        }
      }
    })
  ]

  depends_on = [helm_release.istio_base]
}

# Istio Gateway for Epic 8
resource "kubernetes_manifest" "epic8_gateway" {
  count = var.enable_istio ? 1 : 0

  manifest = {
    apiVersion = "networking.istio.io/v1beta1"
    kind       = "Gateway"
    metadata = {
      name      = "epic8-gateway"
      namespace = "epic8"
      labels    = merge(local.common_labels, {
        "epic8.io/service" = "gateway"
      })
    }
    spec = {
      selector = {
        istio = "ingressgateway"
      }
      servers = concat(
        var.enable_tls ? [
          {
            port = {
              number   = 443
              name     = "https"
              protocol = "HTTPS"
            }
            tls = {
              mode = "SIMPLE"
              credentialName = "epic8-tls-secret"
            }
            hosts = var.gateway_hosts
          }
        ] : [],
        [
          {
            port = {
              number   = 80
              name     = "http"
              protocol = "HTTP"
            }
            hosts = var.gateway_hosts
          }
        ]
      )
    }
  }

  depends_on = [helm_release.istiod]
}

# MetalLB for bare metal deployments (if enabled)
resource "helm_release" "metallb" {
  count = var.enable_metallb ? 1 : 0

  name       = "metallb"
  repository = "https://metallb.github.io/metallb"
  chart      = "metallb"
  namespace  = var.networking_namespace
  version    = "0.13.12"

  values = [
    yamlencode({
      speaker = {
        resources = {
          requests = {
            cpu    = "100m"
            memory = "100Mi"
          }
          limits = {
            cpu    = "100m"
            memory = "100Mi"
          }
        }

        # Security context
        securityContext = {
          runAsNonRoot = false  # Required for MetalLB speaker
          runAsUser    = 0
          capabilities = {
            drop = ["ALL"]
            add  = ["NET_ADMIN", "NET_RAW", "SYS_ADMIN"]
          }
        }
      }

      controller = {
        resources = {
          requests = {
            cpu    = "100m"
            memory = "100Mi"
          }
          limits = {
            cpu    = "100m"
            memory = "100Mi"
          }
        }

        # Security context
        securityContext = {
          runAsNonRoot = true
          runAsUser    = 65534
          capabilities = {
            drop = ["ALL"]
          }
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.networking]
}

# MetalLB IPAddressPool configuration
resource "kubernetes_manifest" "metallb_ip_pool" {
  count = var.enable_metallb ? 1 : 0

  manifest = {
    apiVersion = "metallb.io/v1beta1"
    kind       = "IPAddressPool"
    metadata = {
      name      = "epic8-ip-pool"
      namespace = var.networking_namespace
      labels    = local.common_labels
    }
    spec = {
      addresses = var.metallb_ip_range
    }
  }

  depends_on = [helm_release.metallb]
}

# MetalLB L2Advertisement
resource "kubernetes_manifest" "metallb_l2_advertisement" {
  count = var.enable_metallb ? 1 : 0

  manifest = {
    apiVersion = "metallb.io/v1beta1"
    kind       = "L2Advertisement"
    metadata = {
      name      = "epic8-l2-advertisement"
      namespace = var.networking_namespace
      labels    = local.common_labels
    }
    spec = {
      ipAddressPools = ["epic8-ip-pool"]
    }
  }

  depends_on = [kubernetes_manifest.metallb_ip_pool]
}

# Cert-manager for TLS certificate management (if enabled)
resource "helm_release" "cert_manager" {
  count = var.enable_cert_manager ? 1 : 0

  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  namespace  = "cert-manager"
  version    = "1.13.2"

  create_namespace = true

  set {
    name  = "installCRDs"
    value = "true"
  }

  values = [
    yamlencode({
      global = {
        logLevel = 2
      }

      resources = {
        requests = {
          cpu    = "100m"
          memory = "128Mi"
        }
        limits = {
          cpu    = "500m"
          memory = "512Mi"
        }
      }

      # Security context
      securityContext = {
        runAsNonRoot = true
        runAsUser    = 1001
        runAsGroup   = 1001
        capabilities = {
          drop = ["ALL"]
        }
      }

      # Monitoring
      prometheus = {
        enabled = var.enable_metrics
        servicemonitor = {
          enabled = var.enable_metrics
          namespace = var.monitoring_namespace
          labels = {
            "epic8.io/monitor" = "true"
          }
        }
      }

      webhook = {
        resources = {
          requests = {
            cpu    = "100m"
            memory = "128Mi"
          }
          limits = {
            cpu    = "100m"
            memory = "128Mi"
          }
        }

        securityContext = {
          runAsNonRoot = true
          runAsUser    = 1001
          runAsGroup   = 1001
        }
      }

      cainjector = {
        resources = {
          requests = {
            cpu    = "100m"
            memory = "128Mi"
          }
          limits = {
            cpu    = "100m"
            memory = "128Mi"
          }
        }

        securityContext = {
          runAsNonRoot = true
          runAsUser    = 1001
          runAsGroup   = 1001
        }
      }
    })
  ]
}

# ClusterIssuer for Let's Encrypt (if cert-manager is enabled)
resource "kubernetes_manifest" "letsencrypt_issuer" {
  count = var.enable_cert_manager ? 1 : 0

  manifest = {
    apiVersion = "cert-manager.io/v1"
    kind       = "ClusterIssuer"
    metadata = {
      name   = "letsencrypt-${var.environment}"
      labels = local.common_labels
    }
    spec = {
      acme = {
        server = var.environment == "prod" ? "https://acme-v02.api.letsencrypt.org/directory" : "https://acme-staging-v02.api.letsencrypt.org/directory"
        email  = var.acme_email
        privateKeySecretRef = {
          name = "letsencrypt-${var.environment}-private-key"
        }
        solvers = [
          {
            http01 = {
              ingress = {
                class = var.ingress_class_name
              }
            }
          }
        ]
      }
    }
  }

  depends_on = [helm_release.cert_manager]
}