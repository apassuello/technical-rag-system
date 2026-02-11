# Shared Security Module Variables
# Swiss Engineering Standards: Defense-in-Depth Security Configuration

# Core Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "security_namespace" {
  description = "Kubernetes namespace for security components"
  type        = string
  default     = "security"
}

variable "monitoring_namespace" {
  description = "Kubernetes namespace for monitoring components"
  type        = string
  default     = "monitoring"
}

# Swiss Compliance
variable "swiss_compliance_enabled" {
  description = "Enable Swiss/GDPR compliance configurations"
  type        = bool
  default     = true
}

variable "security_level" {
  description = "Security level: basic, enhanced, maximum"
  type        = string
  default     = "enhanced"

  validation {
    condition     = contains(["basic", "enhanced", "maximum"], var.security_level)
    error_message = "Security level must be one of: basic, enhanced, maximum."
  }
}

# Pod Security Standards
variable "enable_pod_security_standards" {
  description = "Enable Pod Security Standards enforcement"
  type        = bool
  default     = true
}

variable "pod_security_standard" {
  description = "Pod Security Standard to enforce (privileged, baseline, restricted)"
  type        = string
  default     = "restricted"

  validation {
    condition     = contains(["privileged", "baseline", "restricted"], var.pod_security_standard)
    error_message = "Pod Security Standard must be one of: privileged, baseline, restricted."
  }
}

# Network Policies
variable "enable_network_policies" {
  description = "Enable Kubernetes Network Policies"
  type        = bool
  default     = true
}

variable "network_policy_mode" {
  description = "Network policy mode: permissive, restrictive, zero-trust"
  type        = string
  default     = "restrictive"

  validation {
    condition     = contains(["permissive", "restrictive", "zero-trust"], var.network_policy_mode)
    error_message = "Network policy mode must be one of: permissive, restrictive, zero-trust."
  }
}

# RBAC Configuration
variable "enable_rbac" {
  description = "Enable Role-Based Access Control for Epic 8 services"
  type        = bool
  default     = true
}

variable "rbac_mode" {
  description = "RBAC mode: basic, enhanced, maximum"
  type        = string
  default     = "enhanced"

  validation {
    condition     = contains(["basic", "enhanced", "maximum"], var.rbac_mode)
    error_message = "RBAC mode must be one of: basic, enhanced, maximum."
  }
}

# Workload Identity
variable "enable_workload_identity" {
  description = "Enable Workload Identity for cloud provider authentication"
  type        = bool
  default     = false
}

variable "workload_identity_client_ids" {
  description = "Map of service names to Workload Identity client IDs"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# Secret Management
variable "epic8_secrets" {
  description = "Epic 8 application secrets"
  type        = map(map(string))
  default     = {}
  sensitive   = true
}

variable "enable_sealed_secrets" {
  description = "Enable Sealed Secrets controller"
  type        = bool
  default     = false
}

variable "enable_external_secrets" {
  description = "Enable External Secrets Operator"
  type        = bool
  default     = false
}

variable "external_secret_stores" {
  description = "External secret store configurations"
  type = map(object({
    provider = string
    config   = map(any)
  }))
  default = {}
}

# Runtime Security
variable "enable_falco" {
  description = "Enable Falco runtime security"
  type        = bool
  default     = false
}

variable "falco_rules" {
  description = "Custom Falco rules for Epic 8"
  type        = list(string)
  default     = []
}

variable "falco_outputs" {
  description = "Falco output configurations"
  type = map(object({
    enabled = bool
    config  = map(any)
  }))
  default = {
    syslog = {
      enabled = false
      config  = {}
    }
    file = {
      enabled = true
      config = {
        keep_alive = false
        filename   = "/var/log/falco/events.log"
      }
    }
    stdout = {
      enabled = true
      config  = {}
    }
    grpc = {
      enabled = false
      config = {
        address    = "localhost:5060"
        threadiness = 8
      }
    }
  }
}

# Policy Enforcement
variable "enable_gatekeeper" {
  description = "Enable OPA Gatekeeper policy enforcement"
  type        = bool
  default     = false
}

variable "opa_policies" {
  description = "OPA Gatekeeper policies"
  type = map(object({
    crd = object({
      spec = object({
        names = object({
          kind = string
        })
        validation = object({
          openAPIV3Schema = map(any)
        })
      })
    })
    targets = list(object({
      target = string
      rego   = string
    }))
  }))
  default = {}
}

variable "policy_violations_action" {
  description = "Action for policy violations: warn, enforce"
  type        = string
  default     = "enforce"

  validation {
    condition     = contains(["warn", "enforce"], var.policy_violations_action)
    error_message = "Policy violations action must be either warn or enforce."
  }
}

# Image Security
variable "enable_image_scanning" {
  description = "Enable container image security scanning"
  type        = bool
  default     = true
}

variable "allowed_registries" {
  description = "List of allowed container registries"
  type        = list(string)
  default = [
    "docker.io",
    "gcr.io",
    "registry.k8s.io",
    "quay.io"
  ]
}

variable "image_scan_on_push" {
  description = "Enable image scanning on push to registry"
  type        = bool
  default     = true
}

# Certificate Management
variable "enable_cert_manager" {
  description = "Enable cert-manager for certificate management"
  type        = bool
  default     = false
}

variable "cert_manager_issuer" {
  description = "cert-manager issuer configuration"
  type = object({
    name  = string
    kind  = string
    email = string
    server = string
  })
  default = {
    name   = "letsencrypt-prod"
    kind   = "ClusterIssuer"
    email  = "admin@example.com"
    server = "https://acme-v02.api.letsencrypt.org/directory"
  }
}

# Admission Controllers
variable "admission_controllers" {
  description = "Additional admission controllers configuration"
  type = map(object({
    enabled = bool
    config  = map(any)
  }))
  default = {}
}

# Security Scanning
variable "enable_vulnerability_scanning" {
  description = "Enable vulnerability scanning for workloads"
  type        = bool
  default     = true
}

variable "vulnerability_scan_schedule" {
  description = "Cron schedule for vulnerability scanning"
  type        = string
  default     = "0 2 * * *"  # Daily at 2 AM
}

# Compliance
variable "compliance_frameworks" {
  description = "Compliance frameworks to enforce"
  type        = list(string)
  default     = ["gdpr", "iso27001"]
}

variable "audit_logging_enabled" {
  description = "Enable audit logging for security events"
  type        = bool
  default     = true
}

variable "audit_log_retention_days" {
  description = "Audit log retention period in days"
  type        = number
  default     = 90

  validation {
    condition     = var.audit_log_retention_days >= 30 && var.audit_log_retention_days <= 365
    error_message = "Audit log retention days must be between 30 and 365."
  }
}

# Encryption
variable "enable_encryption_at_rest" {
  description = "Enable encryption at rest for secrets and data"
  type        = bool
  default     = true
}

variable "enable_encryption_in_transit" {
  description = "Enable encryption in transit (mTLS)"
  type        = bool
  default     = true
}

variable "encryption_algorithm" {
  description = "Encryption algorithm for data at rest"
  type        = string
  default     = "AES-256-GCM"

  validation {
    condition = contains([
      "AES-128-GCM", "AES-192-GCM", "AES-256-GCM",
      "ChaCha20-Poly1305"
    ], var.encryption_algorithm)
    error_message = "Encryption algorithm must be a supported algorithm."
  }
}

# Monitoring Integration
variable "enable_monitoring" {
  description = "Enable monitoring for security components"
  type        = bool
  default     = true
}

variable "security_metrics_retention" {
  description = "Security metrics retention period"
  type        = string
  default     = "30d"
}

# Alerting
variable "enable_security_alerting" {
  description = "Enable security alerting"
  type        = bool
  default     = true
}

variable "security_alert_webhooks" {
  description = "Webhook URLs for security alerts"
  type        = list(string)
  default     = []
  sensitive   = true
}

variable "critical_alert_channels" {
  description = "Alert channels for critical security events"
  type        = list(string)
  default     = ["email", "slack"]
}

# Resource Limits
variable "security_component_resources" {
  description = "Resource limits for security components"
  type = map(object({
    requests = object({
      cpu    = string
      memory = string
    })
    limits = object({
      cpu    = string
      memory = string
    })
  }))
  default = {
    falco = {
      requests = {
        cpu    = "100m"
        memory = "512Mi"
      }
      limits = {
        cpu    = "1000m"
        memory = "1Gi"
      }
    }
    gatekeeper = {
      requests = {
        cpu    = "100m"
        memory = "256Mi"
      }
      limits = {
        cpu    = "1000m"
        memory = "512Mi"
      }
    }
    sealed_secrets = {
      requests = {
        cpu    = "50m"
        memory = "64Mi"
      }
      limits = {
        cpu    = "200m"
        memory = "256Mi"
      }
    }
  }
}

# Additional Labels
variable "additional_labels" {
  description = "Additional labels to apply to all security resources"
  type        = map(string)
  default     = {}
}