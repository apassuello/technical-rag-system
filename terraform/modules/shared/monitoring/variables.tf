# Shared Monitoring Module Variables
# Swiss Engineering Standards: Comprehensive Observability Configuration

# Core Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "cluster_name" {
  description = "Name of the Kubernetes cluster"
  type        = string
}

variable "monitoring_namespace" {
  description = "Kubernetes namespace for monitoring stack"
  type        = string
  default     = "monitoring"
}

# Swiss Compliance
variable "swiss_compliance_enabled" {
  description = "Enable Swiss/GDPR compliance configurations"
  type        = bool
  default     = true
}

# Component Toggles
variable "enable_prometheus" {
  description = "Enable Prometheus monitoring"
  type        = bool
  default     = true
}

variable "enable_grafana" {
  description = "Enable Grafana dashboards"
  type        = bool
  default     = true
}

variable "enable_alertmanager" {
  description = "Enable AlertManager for alerting"
  type        = bool
  default     = true
}

variable "enable_jaeger" {
  description = "Enable Jaeger distributed tracing"
  type        = bool
  default     = true
}

variable "enable_opentelemetry" {
  description = "Enable OpenTelemetry collector"
  type        = bool
  default     = true
}

variable "enable_node_exporter" {
  description = "Enable Node Exporter for node metrics"
  type        = bool
  default     = true
}

# Storage Configuration
variable "storage_class" {
  description = "Storage class for persistent volumes"
  type        = string
  default     = "standard"
}

# Image Configuration
variable "image_registry" {
  description = "Container image registry (for air-gapped environments)"
  type        = string
  default     = ""
}

# Ingress Configuration
variable "enable_ingress" {
  description = "Enable ingress for monitoring services"
  type        = bool
  default     = false
}

variable "ingress_class" {
  description = "Ingress class name"
  type        = string
  default     = "nginx"
}

variable "domain_name" {
  description = "Domain name for ingress hosts"
  type        = string
  default     = "example.com"
}

variable "enable_tls" {
  description = "Enable TLS for ingress"
  type        = bool
  default     = true
}

variable "ingress_annotations" {
  description = "Additional annotations for ingress resources"
  type        = map(string)
  default     = {}
}

# Authentication Configuration
variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "enable_oauth" {
  description = "Enable OAuth authentication for Grafana"
  type        = bool
  default     = false
}

variable "oauth_client_id" {
  description = "OAuth client ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "oauth_client_secret" {
  description = "OAuth client secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "oauth_auth_url" {
  description = "OAuth authorization URL"
  type        = string
  default     = ""
}

variable "oauth_token_url" {
  description = "OAuth token URL"
  type        = string
  default     = ""
}

variable "oauth_api_url" {
  description = "OAuth API URL"
  type        = string
  default     = ""
}

# Alerting Configuration
variable "alert_webhook_url" {
  description = "Webhook URL for alerts (Slack, Teams, etc.)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "alert_email_to" {
  description = "Email address for alert notifications"
  type        = string
  default     = ""
}

variable "alert_email_from" {
  description = "Email address for sending alerts"
  type        = string
  default     = ""
}

variable "smtp_server" {
  description = "SMTP server for email alerts"
  type        = string
  default     = ""
}

variable "smtp_port" {
  description = "SMTP server port"
  type        = number
  default     = 587
}

variable "smtp_username" {
  description = "SMTP username"
  type        = string
  default     = ""
  sensitive   = true
}

variable "smtp_password" {
  description = "SMTP password"
  type        = string
  default     = ""
  sensitive   = true
}

# Custom Dashboards
variable "custom_dashboards" {
  description = "Custom Grafana dashboards"
  type = map(object({
    json     = string
    folder   = string
    editable = bool
  }))
  default = {}
}

# Custom Alert Rules
variable "custom_alert_rules" {
  description = "Custom Prometheus alert rules"
  type = map(object({
    groups = list(object({
      name  = string
      rules = list(object({
        alert       = string
        expr        = string
        for         = string
        labels      = map(string)
        annotations = map(string)
      }))
    }))
  }))
  default = {}
}

# Epic 8 Specific Configuration
variable "epic8_metrics_endpoints" {
  description = "Epic 8 service metrics endpoints"
  type = map(object({
    namespace = string
    port      = number
    path      = string
  }))
  default = {
    api-gateway = {
      namespace = "epic8"
      port      = 8080
      path      = "/metrics"
    }
    query-analyzer = {
      namespace = "epic8"
      port      = 8081
      path      = "/metrics"
    }
    retriever = {
      namespace = "epic8"
      port      = 8082
      path      = "/metrics"
    }
    generator = {
      namespace = "epic8"
      port      = 8083
      path      = "/metrics"
    }
    cache = {
      namespace = "epic8"
      port      = 8084
      path      = "/metrics"
    }
    analytics = {
      namespace = "epic8"
      port      = 8085
      path      = "/metrics"
    }
  }
}

# Resource Limits
variable "prometheus_resources" {
  description = "Resource limits for Prometheus"
  type = object({
    requests = object({
      cpu    = string
      memory = string
    })
    limits = object({
      cpu    = string
      memory = string
    })
  })
  default = {
    requests = {
      cpu    = "500m"
      memory = "2Gi"
    }
    limits = {
      cpu    = "4"
      memory = "8Gi"
    }
  }
}

variable "grafana_resources" {
  description = "Resource limits for Grafana"
  type = object({
    requests = object({
      cpu    = string
      memory = string
    })
    limits = object({
      cpu    = string
      memory = string
    })
  })
  default = {
    requests = {
      cpu    = "100m"
      memory = "256Mi"
    }
    limits = {
      cpu    = "500m"
      memory = "1Gi"
    }
  }
}

# Data Retention
variable "prometheus_retention_size" {
  description = "Prometheus data retention size"
  type        = string
  default     = ""
}

variable "jaeger_retention_days" {
  description = "Jaeger trace retention in days"
  type        = number
  default     = 7

  validation {
    condition     = var.jaeger_retention_days >= 1 && var.jaeger_retention_days <= 90
    error_message = "Jaeger retention days must be between 1 and 90."
  }
}

# High Availability
variable "enable_high_availability" {
  description = "Enable high availability mode for monitoring components"
  type        = bool
  default     = false
}

variable "prometheus_replicas" {
  description = "Number of Prometheus replicas (HA mode)"
  type        = number
  default     = 1

  validation {
    condition     = var.prometheus_replicas >= 1 && var.prometheus_replicas <= 5
    error_message = "Prometheus replicas must be between 1 and 5."
  }
}

variable "grafana_replicas" {
  description = "Number of Grafana replicas (HA mode)"
  type        = number
  default     = 1

  validation {
    condition     = var.grafana_replicas >= 1 && var.grafana_replicas <= 3
    error_message = "Grafana replicas must be between 1 and 3."
  }
}

# External Services
variable "external_prometheus_url" {
  description = "External Prometheus URL for federation"
  type        = string
  default     = ""
}

variable "external_grafana_url" {
  description = "External Grafana URL for dashboards"
  type        = string
  default     = ""
}

variable "external_jaeger_url" {
  description = "External Jaeger URL for tracing"
  type        = string
  default     = ""
}

# Security
variable "enable_pod_security_policy" {
  description = "Enable Pod Security Policy for monitoring components"
  type        = bool
  default     = true
}

variable "enable_network_policy" {
  description = "Enable Network Policy for monitoring components"
  type        = bool
  default     = true
}

variable "enable_rbac" {
  description = "Enable RBAC for monitoring components"
  type        = bool
  default     = true
}

# Additional Labels
variable "additional_labels" {
  description = "Additional labels to apply to all monitoring resources"
  type        = map(string)
  default     = {}
}