# Epic 8: Cloud-Native Microservices Architecture (Archived)

This directory contains the microservices deployment layer for the RAG system.
It was developed as Epic 8 (Cloud-Native Multi-Model RAG Platform) and archived
on 2026-02-11 when the project shifted to a local-first architecture.

## Why Archived
The core RAG system in src/ is a complete, self-contained application. The 6
microservices were thin FastAPI wrappers that added deployment complexity without
adding functionality. The decision to archive was based on:
- Portfolio alignment with ML Engineer roles (not DevOps)
- All 378 microservices tests were broken/skipped for 5+ months
- The Kind K8s cluster had fundamental networking failures (CoreDNS timeout)
- Core tests (2,109) cover all ML/RAG capabilities without Docker

## What's Here
- services/ — 5 FastAPI microservices (api-gateway, generator, retriever, query-analyzer, analytics)
- helm/ — Kubernetes Helm charts with dev/staging/prod configs
- k8s/ — Raw Kubernetes manifests (deployments, HPA, ingress, RBAC, storage, monitoring)
- terraform/ — Multi-cloud IaC (AWS EKS, Azure AKS, GCP GKE)
- deployment/ — ECS deployment scripts
- tests/epic8/ — Unit, integration, API, and performance tests
- scripts/ — Epic 8 profiling, deployment, k8s-testing, verification scripts
- github-workflows/ — CI workflows for k8s and helm testing
- docker-compose.original.yml — Original 9-service compose configuration

## Restoration
To restore: copy contents back to project root, rebuild Docker images, fix Kind cluster.
See: docs/plans/plan-a-cloud-native-microservices.md
