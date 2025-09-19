{{/*
Epic 8 Platform - Helm Template Helpers
Swiss Engineering Quality Standards for Kubernetes Templates
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "epic8-platform.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "epic8-platform.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "epic8-platform.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the namespace to use
*/}}
{{- define "epic8-platform.namespace" -}}
{{- if .Values.namespace.name -}}
{{- .Values.namespace.name }}
{{- else -}}
{{- .Release.Namespace }}
{{- end -}}
{{- end }}

{{/*
Common labels for all Epic 8 Platform resources
*/}}
{{- define "epic8-platform.labels" -}}
helm.sh/chart: {{ include "epic8-platform.chart" . }}
{{ include "epic8-platform.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
epic8.platform/version: v1
epic8.platform/platform: {{ .Values.global.platform.name }}
epic8.platform/environment: {{ .Values.global.environment }}
epic8.platform/compliance: swiss-engineering
{{- end }}

{{/*
Selector labels
*/}}
{{- define "epic8-platform.selectorLabels" -}}
app.kubernetes.io/name: {{ include "epic8-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common Epic 8 Platform annotations
*/}}
{{- define "epic8-platform.annotations" -}}
epic8.platform/deployment-time: {{ now | quote }}
epic8.platform/chart-version: {{ .Chart.Version | quote }}
epic8.platform/app-version: {{ .Chart.AppVersion | quote }}
epic8.platform/environment: {{ .Values.global.environment | quote }}
{{- if .Values.global.platform.description }}
epic8.platform/description: {{ .Values.global.platform.description | quote }}
{{- end }}
{{- end }}

{{/*
===============================================================================
Service-Specific Template Helpers
===============================================================================
*/}}

{{/*
Create service name helper
Usage: {{ include "epic8-platform.serviceName" (dict "service" "api-gateway" "context" .) }}
*/}}
{{- define "epic8-platform.serviceName" -}}
{{- $serviceName := .service -}}
{{- $fullname := include "epic8-platform.fullname" .context -}}
{{- printf "%s-%s" $fullname $serviceName | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Service labels for specific services
Usage: {{ include "epic8-platform.serviceLabels" (dict "service" "api-gateway" "tier" "frontend" "component" "gateway" "context" .) }}
*/}}
{{- define "epic8-platform.serviceLabels" -}}
{{ include "epic8-platform.labels" .context }}
epic8.platform/service: {{ .service }}
epic8.platform/tier: {{ .tier }}
epic8.platform/component: {{ .component }}
app.kubernetes.io/name: {{ .service }}
app.kubernetes.io/part-of: epic8-platform
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Service selector labels
Usage: {{ include "epic8-platform.serviceSelectorLabels" (dict "service" "api-gateway" "context" .) }}
*/}}
{{- define "epic8-platform.serviceSelectorLabels" -}}
epic8.platform/service: {{ .service }}
app.kubernetes.io/name: {{ .service }}
app.kubernetes.io/instance: {{ .context.Release.Name }}
{{- end }}

{{/*
===============================================================================
Resource Management Helpers
===============================================================================
*/}}

{{/*
Get resource configuration for a service
Usage: {{ include "epic8-platform.resources" (dict "service" .Values.apiGateway "global" .Values.global "context" .) }}
*/}}
{{- define "epic8-platform.resources" -}}
{{- $resources := .service.resources -}}
{{- if typeIs "string" $resources -}}
{{- $resourceType := $resources -}}
{{- if eq $resourceType "small" -}}
{{- toYaml .global.resources.small -}}
{{- else if eq $resourceType "medium" -}}
{{- toYaml .global.resources.medium -}}
{{- else if eq $resourceType "large" -}}
{{- toYaml .global.resources.large -}}
{{- else -}}
{{- toYaml .global.resources.medium -}}
{{- end -}}
{{- else -}}
{{- toYaml $resources -}}
{{- end -}}
{{- end }}

{{/*
===============================================================================
Security Context Helpers
===============================================================================
*/}}

{{/*
Pod security context with Swiss engineering standards
Usage: {{ include "epic8-platform.podSecurityContext" . }}
*/}}
{{- define "epic8-platform.podSecurityContext" -}}
runAsNonRoot: {{ .Values.global.security.runAsNonRoot }}
runAsUser: {{ .Values.global.security.runAsUser }}
runAsGroup: {{ .Values.global.security.runAsGroup }}
fsGroup: {{ .Values.global.security.fsGroup }}
seccompProfile:
  type: {{ .Values.global.security.seccompProfile.type }}
{{- end }}

{{/*
Container security context
Usage: {{ include "epic8-platform.containerSecurityContext" . }}
*/}}
{{- define "epic8-platform.containerSecurityContext" -}}
allowPrivilegeEscalation: {{ .Values.global.security.allowPrivilegeEscalation }}
readOnlyRootFilesystem: {{ .Values.global.security.readOnlyRootFilesystem }}
capabilities:
  drop:
  {{- range .Values.global.security.capabilities.drop }}
  - {{ . }}
  {{- end }}
{{- end }}

{{/*
===============================================================================
Environment Variables Helpers
===============================================================================
*/}}

{{/*
Common environment variables for all services
Usage: {{ include "epic8-platform.commonEnvVars" . }}
*/}}
{{- define "epic8-platform.commonEnvVars" -}}
- name: PYTHONPATH
  value: "/app:/app/src"
- name: PROJECT_ROOT
  value: "/app"
- name: KUBERNETES_NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: POD_IP
  valueFrom:
    fieldRef:
      fieldPath: status.podIP
- name: NODE_NAME
  valueFrom:
    fieldRef:
      fieldPath: spec.nodeName
{{- end }}

{{/*
Service discovery environment variables
Usage: {{ include "epic8-platform.serviceDiscoveryEnvVars" . }}
*/}}
{{- define "epic8-platform.serviceDiscoveryEnvVars" -}}
- name: QUERY_ANALYZER_URL
  value: "http://{{ include "epic8-platform.serviceName" (dict "service" "query-analyzer" "context" .) }}:8082"
- name: GENERATOR_URL
  value: "http://{{ include "epic8-platform.serviceName" (dict "service" "generator" "context" .) }}:8081"
- name: RETRIEVER_URL
  value: "http://{{ include "epic8-platform.serviceName" (dict "service" "retriever" "context" .) }}:8083"
- name: CACHE_URL
  value: "http://{{ include "epic8-platform.serviceName" (dict "service" "cache" "context" .) }}:8084"
- name: ANALYTICS_URL
  value: "http://{{ include "epic8-platform.serviceName" (dict "service" "analytics" "context" .) }}:8085"
{{- end }}

{{/*
===============================================================================
Health Check Helpers
===============================================================================
*/}}

{{/*
HTTP health check probe
Usage: {{ include "epic8-platform.httpProbe" (dict "path" "/health/live" "port" "http" "config" .Values.apiGateway.health.liveness) }}
*/}}
{{- define "epic8-platform.httpProbe" -}}
httpGet:
  path: {{ .path }}
  port: {{ .port }}
  scheme: HTTP
initialDelaySeconds: {{ .config.initialDelaySeconds }}
periodSeconds: {{ .config.periodSeconds }}
timeoutSeconds: {{ .config.timeoutSeconds }}
successThreshold: {{ default 1 .config.successThreshold }}
failureThreshold: {{ .config.failureThreshold }}
{{- end }}

{{/*
===============================================================================
Volume Helpers
===============================================================================
*/}}

{{/*
Standard temporary volumes for Epic 8 services
Usage: {{ include "epic8-platform.standardVolumes" . }}
*/}}
{{- define "epic8-platform.standardVolumes" -}}
- name: tmp
  emptyDir: {}
- name: var-run
  emptyDir: {}
- name: logs
  emptyDir: {}
- name: cache
  emptyDir: {}
{{- end }}

{{/*
Standard volume mounts for Epic 8 services
Usage: {{ include "epic8-platform.standardVolumeMounts" . }}
*/}}
{{- define "epic8-platform.standardVolumeMounts" -}}
- name: tmp
  mountPath: /tmp
- name: var-run
  mountPath: /var/run
- name: logs
  mountPath: /app/logs
- name: cache
  mountPath: /app/cache
{{- end }}

{{/*
===============================================================================
Monitoring and Observability Helpers
===============================================================================
*/}}

{{/*
Prometheus monitoring annotations
Usage: {{ include "epic8-platform.prometheusAnnotations" (dict "port" "9090" "path" "/metrics") }}
*/}}
{{- define "epic8-platform.prometheusAnnotations" -}}
prometheus.io/scrape: "true"
prometheus.io/port: {{ .port | quote }}
prometheus.io/path: {{ .path | quote }}
{{- end }}

{{/*
Service mesh annotations (Istio)
Usage: {{ include "epic8-platform.serviceMeshAnnotations" . }}
*/}}
{{- define "epic8-platform.serviceMeshAnnotations" -}}
{{- if .Values.global.serviceMesh.enabled }}
{{- if eq .Values.global.serviceMesh.type "istio" }}
sidecar.istio.io/inject: "true"
{{- if .Values.global.serviceMesh.tracing.enabled }}
sidecar.istio.io/proxyCPU: "100m"
sidecar.istio.io/proxyMemory: "128Mi"
{{- end }}
{{- end }}
{{- end }}
{{- end }}

{{/*
===============================================================================
Affinity and Topology Helpers
===============================================================================
*/}}

{{/*
Pod anti-affinity rules for high availability
Usage: {{ include "epic8-platform.podAntiAffinity" (dict "service" "api-gateway" "weight" 100 "required" false) }}
*/}}
{{- define "epic8-platform.podAntiAffinity" -}}
{{- if .required }}
requiredDuringSchedulingIgnoredDuringExecution:
- labelSelector:
    matchExpressions:
    - key: epic8.platform/service
      operator: In
      values:
      - {{ .service }}
  topologyKey: kubernetes.io/hostname
{{- else }}
preferredDuringSchedulingIgnoredDuringExecution:
- weight: {{ .weight }}
  podAffinityTerm:
    labelSelector:
      matchExpressions:
      - key: epic8.platform/service
        operator: In
        values:
        - {{ .service }}
    topologyKey: kubernetes.io/hostname
{{- end }}
{{- end }}

{{/*
Topology spread constraints for even distribution
Usage: {{ include "epic8-platform.topologySpreadConstraints" (dict "service" "api-gateway" "maxSkew" 1) }}
*/}}
{{- define "epic8-platform.topologySpreadConstraints" -}}
- maxSkew: {{ .maxSkew }}
  topologyKey: kubernetes.io/hostname
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      epic8.platform/service: {{ .service }}
- maxSkew: {{ .maxSkew }}
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: ScheduleAnyway
  labelSelector:
    matchLabels:
      epic8.platform/service: {{ .service }}
{{- end }}

{{/*
===============================================================================
Auto-scaling Helpers
===============================================================================
*/}}

{{/*
HPA configuration
Usage: {{ include "epic8-platform.hpaSpec" (dict "service" .Values.apiGateway "serviceName" "api-gateway" "context" .) }}
*/}}
{{- define "epic8-platform.hpaSpec" -}}
scaleTargetRef:
  apiVersion: apps/v1
  kind: Deployment
  name: {{ include "epic8-platform.serviceName" (dict "service" .serviceName "context" .context) }}
minReplicas: {{ .service.autoscaling.minReplicas }}
maxReplicas: {{ .service.autoscaling.maxReplicas }}
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: {{ .service.autoscaling.targetCPUUtilizationPercentage }}
- type: Resource
  resource:
    name: memory
    target:
      type: Utilization
      averageUtilization: {{ .service.autoscaling.targetMemoryUtilizationPercentage }}
{{- if .service.autoscaling.behavior }}
behavior:
{{ toYaml .service.autoscaling.behavior | indent 2 }}
{{- end }}
{{- end }}

{{/*
===============================================================================
Network Policy Helpers
===============================================================================
*/}}

{{/*
Network policy selector
Usage: {{ include "epic8-platform.networkPolicySelector" (dict "service" "api-gateway") }}
*/}}
{{- define "epic8-platform.networkPolicySelector" -}}
podSelector:
  matchLabels:
    epic8.platform/service: {{ .service }}
{{- end }}

{{/*
===============================================================================
Storage Helpers
===============================================================================
*/}}

{{/*
Persistent volume claim template
Usage: {{ include "epic8-platform.pvcTemplate" (dict "name" "data" "size" "10Gi" "storageClass" "epic8-ssd" "accessModes" (list "ReadWriteOnce")) }}
*/}}
{{- define "epic8-platform.pvcTemplate" -}}
metadata:
  name: {{ .name }}
spec:
  accessModes:
  {{- range .accessModes }}
  - {{ . }}
  {{- end }}
  {{- if .storageClass }}
  storageClassName: {{ .storageClass }}
  {{- end }}
  resources:
    requests:
      storage: {{ .size }}
{{- end }}

{{/*
===============================================================================
Configuration Helpers
===============================================================================
*/}}

{{/*
External secret reference
Usage: {{ include "epic8-platform.secretKeyRef" (dict "secret" "epic8-secrets" "key" "api-key") }}
*/}}
{{- define "epic8-platform.secretKeyRef" -}}
secretKeyRef:
  name: {{ .secret }}
  key: {{ .key }}
{{- end }}

{{/*
ConfigMap reference
Usage: {{ include "epic8-platform.configMapKeyRef" (dict "configMap" "epic8-config" "key" "config-value") }}
*/}}
{{- define "epic8-platform.configMapKeyRef" -}}
configMapKeyRef:
  name: {{ .configMap }}
  key: {{ .key }}
{{- end }}

{{/*
===============================================================================
Image Helpers
===============================================================================
*/}}

{{/*
Container image with registry and tag
Usage: {{ include "epic8-platform.image" (dict "repository" "epic8/api-gateway" "tag" "latest" "global" .Values.global) }}
*/}}
{{- define "epic8-platform.image" -}}
{{- $registry := .global.image.registry -}}
{{- $repository := .repository -}}
{{- $tag := .tag -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else -}}
{{- printf "%s:%s" $repository $tag -}}
{{- end -}}
{{- end }}

{{/*
===============================================================================
Conditional Helpers
===============================================================================
*/}}

{{/*
Check if monitoring is enabled
Usage: {{ if include "epic8-platform.monitoring.enabled" . }}
*/}}
{{- define "epic8-platform.monitoring.enabled" -}}
{{- if .Values.global.monitoring.enabled -}}
true
{{- end -}}
{{- end }}

{{/*
Check if service mesh is enabled
Usage: {{ if include "epic8-platform.serviceMesh.enabled" . }}
*/}}
{{- define "epic8-platform.serviceMesh.enabled" -}}
{{- if .Values.global.serviceMesh.enabled -}}
true
{{- end -}}
{{- end }}

{{/*
Check if autoscaling is enabled for a service
Usage: {{ if include "epic8-platform.autoscaling.enabled" .Values.apiGateway }}
*/}}
{{- define "epic8-platform.autoscaling.enabled" -}}
{{- if .autoscaling.enabled -}}
true
{{- end -}}
{{- end }}

{{/*
Check if external service is enabled
Usage: {{ if include "epic8-platform.external.enabled" .Values.apiGateway.service }}
*/}}
{{- define "epic8-platform.external.enabled" -}}
{{- if .external.enabled -}}
true
{{- end -}}
{{- end }}

{{/*
===============================================================================
Validation Helpers
===============================================================================
*/}}

{{/*
Validate Epic 8 configuration
Usage: {{ include "epic8-platform.validate" . }}
*/}}
{{- define "epic8-platform.validate" -}}
{{- if not .Values.global.environment -}}
{{- fail "global.environment is required" -}}
{{- end -}}
{{- if not (has .Values.global.environment (list "development" "staging" "production")) -}}
{{- fail "global.environment must be one of: development, staging, production" -}}
{{- end -}}
{{- if not .Values.global.cloudProvider -}}
{{- fail "global.cloudProvider is required" -}}
{{- end -}}
{{- if not (has .Values.global.cloudProvider (list "aws" "gcp" "azure" "on-premises")) -}}
{{- fail "global.cloudProvider must be one of: aws, gcp, azure, on-premises" -}}
{{- end -}}
{{- end }}