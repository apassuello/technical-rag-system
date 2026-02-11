# Shared Security Module for Multi-Cloud Epic 8 Deployment
# Swiss Engineering Standards: Defense-in-Depth Security

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

# Local values for security configuration
locals {
  # Environment-specific security configurations
  security_configs = {
    dev = {
      pod_security_standard = "baseline"
      network_policy_mode   = "permissive"
      rbac_mode            = "basic"
      audit_level         = "minimal"
    }
    staging = {
      pod_security_standard = "restricted"
      network_policy_mode   = "restrictive"
      rbac_mode            = "enhanced"
      audit_level         = "standard"
    }
    prod = {
      pod_security_standard = "restricted"
      network_policy_mode   = "zero-trust"
      rbac_mode            = "maximum"
      audit_level         = "comprehensive"
    }
  }

  current_config = local.security_configs[var.environment]

  # Swiss compliance and security labels
  common_labels = {
    "epic8.io/component"        = "security"
    "epic8.io/environment"      = var.environment
    "epic8.io/managed-by"       = "terraform"
    "epic8.io/swiss-compliance" = var.swiss_compliance_enabled ? "enabled" : "disabled"
    "epic8.io/security-level"   = var.security_level
  }
}

# Security namespace
resource "kubernetes_namespace" "security" {
  metadata {
    name = var.security_namespace
    labels = merge(local.common_labels, {
      "name" = var.security_namespace
      "epic8.io/purpose" = "security"
      "pod-security.kubernetes.io/enforce" = local.current_config.pod_security_standard
      "pod-security.kubernetes.io/audit"   = local.current_config.pod_security_standard
      "pod-security.kubernetes.io/warn"    = local.current_config.pod_security_standard
    })
    annotations = var.swiss_compliance_enabled ? {
      "epic8.io/data-classification" = "confidential"
      "epic8.io/data-residency"     = "eu"
    } : {}
  }
}

# Pod Security Standards enforcement
resource "kubernetes_config_map" "pod_security_standards" {
  count = var.enable_pod_security_standards ? 1 : 0

  metadata {
    name      = "pod-security-standards"
    namespace = var.security_namespace
    labels    = local.common_labels
  }

  data = {
    "policy.yaml" = yamlencode({
      apiVersion = "v1"
      kind       = "ConfigMap"
      metadata = {
        name = "pod-security-standards"
      }
      data = {
        baseline = yamlencode({
          spec = {
            securityContext = {
              runAsNonRoot = true
              runAsUser    = 65534
              runAsGroup   = 65534
              fsGroup      = 65534
            }
            containers = [
              {
                securityContext = {
                  allowPrivilegeEscalation = false
                  readOnlyRootFilesystem   = true
                  capabilities = {
                    drop = ["ALL"]
                  }
                }
              }
            ]
          }
        })
        restricted = yamlencode({
          spec = {
            securityContext = {
              runAsNonRoot = true
              runAsUser    = 65534
              runAsGroup   = 65534
              fsGroup      = 65534
              seccompProfile = {
                type = "RuntimeDefault"
              }
            }
            containers = [
              {
                securityContext = {
                  allowPrivilegeEscalation = false
                  readOnlyRootFilesystem   = true
                  runAsNonRoot            = true
                  capabilities = {
                    drop = ["ALL"]
                  }
                  seccompProfile = {
                    type = "RuntimeDefault"
                  }
                }
              }
            ]
          }
        })
      }
    })
  }

  depends_on = [kubernetes_namespace.security]
}

# Network Policies for Epic 8 services
resource "kubernetes_network_policy" "epic8_default_deny" {
  count = var.enable_network_policies ? 1 : 0

  metadata {
    name      = "epic8-default-deny"
    namespace = "epic8"
    labels    = merge(local.common_labels, {
      "epic8.io/policy-type" = "default-deny"
    })
  }

  spec {
    pod_selector {}
    policy_types = ["Ingress", "Egress"]
  }
}

resource "kubernetes_network_policy" "epic8_allow_internal" {
  count = var.enable_network_policies ? 1 : 0

  metadata {
    name      = "epic8-allow-internal"
    namespace = "epic8"
    labels    = merge(local.common_labels, {
      "epic8.io/policy-type" = "allow-internal"
    })
  }

  spec {
    pod_selector {
      match_labels = {
        "app.kubernetes.io/part-of" = "epic8"
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

    # Allow egress to system services (DNS, monitoring)
    egress {
      to {
        namespace_selector {
          match_labels = {
            name = "kube-system"
          }
        }
      }
    }

    egress {
      to {
        namespace_selector {
          match_labels = {
            name = var.monitoring_namespace
          }
        }
      }
    }

    # Allow DNS resolution
    egress {
      ports {
        protocol = "UDP"
        port     = "53"
      }
      ports {
        protocol = "TCP"
        port     = "53"
      }
    }

    # Allow HTTPS for external API calls
    egress {
      ports {
        protocol = "TCP"
        port     = "443"
      }
    }
  }

  depends_on = [kubernetes_network_policy.epic8_default_deny]
}

# RBAC for Epic 8 services
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
    namespace = "epic8"
    labels    = merge(local.common_labels, {
      "epic8.io/service" = each.key
    })
    annotations = var.enable_workload_identity ? {
      "azure.workload.identity/client-id" = var.workload_identity_client_ids[each.key]
    } : {}
  }
}

resource "kubernetes_role" "epic8_service_role" {
  for_each = var.enable_rbac ? toset([
    "api-gateway",
    "query-analyzer",
    "retriever",
    "generator",
    "cache",
    "analytics"
  ]) : toset([])

  metadata {
    name      = "${each.key}-role"
    namespace = "epic8"
    labels    = local.common_labels
  }

  rule {
    api_groups = [""]
    resources  = ["configmaps", "secrets"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = [""]
    resources  = ["events"]
    verbs      = ["create", "patch"]
  }

  rule {
    api_groups = ["apps"]
    resources  = ["deployments", "replicasets"]
    verbs      = ["get", "list", "watch"]
  }

  # Service-specific permissions
  dynamic "rule" {
    for_each = each.key == "api-gateway" ? [1] : []
    content {
      api_groups = ["networking.k8s.io"]
      resources  = ["ingresses"]
      verbs      = ["get", "list", "watch"]
    }
  }

  dynamic "rule" {
    for_each = each.key == "analytics" ? [1] : []
    content {
      api_groups = [""]
      resources  = ["pods", "services", "endpoints"]
      verbs      = ["get", "list", "watch"]
    }
  }
}

resource "kubernetes_role_binding" "epic8_service_binding" {
  for_each = var.enable_rbac ? toset([
    "api-gateway",
    "query-analyzer",
    "retriever",
    "generator",
    "cache",
    "analytics"
  ]) : toset([])

  metadata {
    name      = "${each.key}-binding"
    namespace = "epic8"
    labels    = local.common_labels
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.epic8_service_role[each.key].metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.epic8_services[each.key].metadata[0].name
    namespace = "epic8"
  }
}

# Secret management for Epic 8
resource "kubernetes_secret" "epic8_secrets" {
  for_each = var.epic8_secrets

  metadata {
    name      = each.key
    namespace = "epic8"
    labels    = merge(local.common_labels, {
      "epic8.io/secret-type" = "application"
    })
    annotations = {
      "epic8.io/encrypted" = "true"
    }
  }

  type = "Opaque"
  data = each.value

  depends_on = [kubernetes_namespace.security]
}

# Sealed Secrets (if enabled)
resource "helm_release" "sealed_secrets" {
  count = var.enable_sealed_secrets ? 1 : 0

  name       = "sealed-secrets"
  repository = "https://bitnami-labs.github.io/sealed-secrets"
  chart      = "sealed-secrets"
  namespace  = var.security_namespace
  version    = "2.13.0"

  values = [
    yamlencode({
      fullnameOverride = "sealed-secrets-controller"

      resources = {
        requests = {
          cpu    = "50m"
          memory = "64Mi"
        }
        limits = {
          cpu    = "200m"
          memory = "256Mi"
        }
      }

      securityContext = {
        runAsNonRoot = true
        runAsUser    = 65534
        runAsGroup   = 65534
        fsGroup      = 65534
      }

      podSecurityContext = {
        seccompProfile = {
          type = "RuntimeDefault"
        }
      }

      serviceMonitor = {
        create = var.enable_monitoring
        labels = {
          "epic8.io/monitor" = "true"
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.security]
}

# External Secrets Operator (if enabled)
resource "helm_release" "external_secrets" {
  count = var.enable_external_secrets ? 1 : 0

  name       = "external-secrets"
  repository = "https://charts.external-secrets.io"
  chart      = "external-secrets"
  namespace  = var.security_namespace
  version    = "0.9.11"

  values = [
    yamlencode({
      installCRDs = true

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

      securityContext = {
        allowPrivilegeEscalation = false
        capabilities = {
          drop = ["ALL"]
        }
        readOnlyRootFilesystem = true
        runAsNonRoot          = true
        runAsUser            = 65534
        runAsGroup           = 65534
      }

      serviceMonitor = {
        enabled = var.enable_monitoring
        labels = {
          "epic8.io/monitor" = "true"
        }
      }

      webhook = {
        create = true
        port   = 9443
      }
    })
  ]

  depends_on = [kubernetes_namespace.security]
}

# Falco for runtime security (if enabled)
resource "helm_release" "falco" {
  count = var.enable_falco ? 1 : 0

  name       = "falco"
  repository = "https://falcosecurity.github.io/charts"
  chart      = "falco"
  namespace  = var.security_namespace
  version    = "3.8.4"

  values = [
    yamlencode({
      driver = {
        kind = "ebpf"
      }

      collectors = {
        enabled = true
      }

      falco = {
        rules_file = [
          "/etc/falco/falco_rules.yaml",
          "/etc/falco/falco_rules.local.yaml",
          "/etc/falco/rules.d"
        ]

        grpc = {
          enabled       = true
          bind_address  = "0.0.0.0:5060"
          thread_pool   = 8
        }

        grpc_output = {
          enabled = true
        }

        json_output = true
        json_include_output_property = true

        # Custom rules for Epic 8
        customRules = {
          "epic8_rules.yaml" = <<-EOF
            - rule: Epic8 Unauthorized File Access
              desc: Detect unauthorized file access in Epic8 containers
              condition: >
                open_read and container and
                container.image.name contains "epic8" and
                fd.name startswith "/etc/" and
                not fd.name in (/etc/passwd, /etc/group, /etc/hostname, /etc/hosts, /etc/resolv.conf)
              output: >
                Unauthorized file read in Epic8 container
                (user=%user.name command=%proc.cmdline file=%fd.name container=%container.name image=%container.image.name)
              priority: WARNING
              tags: [epic8, filesystem, security]

            - rule: Epic8 Network Anomaly
              desc: Detect unexpected network connections from Epic8 services
              condition: >
                inbound and container and
                container.image.name contains "epic8" and
                not fd.sport in (8080, 8081, 8082, 8083, 8084, 8085, 9090, 9091, 9092, 9093, 9094, 9095)
              output: >
                Unexpected network connection in Epic8 service
                (user=%user.name command=%proc.cmdline connection=%fd.name container=%container.name)
              priority: NOTICE
              tags: [epic8, network, security]
          EOF
        }
      }

      falcoctl = {
        config = {
          artifact = {
            install = {
              enabled = true
            }
            follow = {
              enabled = true
            }
          }
        }
      }

      resources = {
        requests = {
          cpu    = "100m"
          memory = "512Mi"
        }
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }

      serviceMonitor = {
        enabled = var.enable_monitoring
        labels = {
          "epic8.io/monitor" = "true"
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.security]
}

# OPA Gatekeeper for policy enforcement (if enabled)
resource "helm_release" "gatekeeper" {
  count = var.enable_gatekeeper ? 1 : 0

  name       = "gatekeeper"
  repository = "https://open-policy-agent.github.io/gatekeeper/charts"
  chart      = "gatekeeper"
  namespace  = "gatekeeper-system"
  version    = "3.14.0"

  create_namespace = true

  values = [
    yamlencode({
      replicas = var.environment == "prod" ? 3 : 1

      resources = {
        requests = {
          cpu    = "100m"
          memory = "256Mi"
        }
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }

      audit = {
        resources = {
          requests = {
            cpu    = "100m"
            memory = "256Mi"
          }
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }

      psp = {
        enabled = false  # Using Pod Security Standards instead
      }

      # Mutation webhook
      mutations = {
        enable = true
      }

      # External data provider
      externalDataProvider = {
        enable = false
      }
    })
  ]
}

# Kustomization for additional security policies
resource "kubernetes_manifest" "security_policies" {
  for_each = var.enable_gatekeeper ? var.opa_policies : {}

  manifest = {
    apiVersion = "templates.gatekeeper.sh/v1beta1"
    kind       = "ConstraintTemplate"
    metadata = {
      name   = each.key
      labels = local.common_labels
    }
    spec = each.value
  }

  depends_on = [helm_release.gatekeeper]
}