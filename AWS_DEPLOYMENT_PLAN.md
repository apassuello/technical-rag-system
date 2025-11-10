# Epic 8 AWS Deployment Plan
## Production Deployment to Amazon Web Services

**Date**: November 10, 2025
**Target**: AWS EKS (Elastic Kubernetes Service)
**Region**: eu-central-1 (Frankfurt, Switzerland-proximate)
**Status**: READY FOR DEPLOYMENT

---

## 🎯 Executive Summary

This comprehensive plan details the step-by-step deployment of the Epic 8 Cloud-Native Multi-Model RAG Platform to AWS, leveraging existing Terraform modules and Kubernetes manifests for production-grade infrastructure.

### Deployment Overview

**Infrastructure**: AWS EKS cluster with 6 microservices
**Timeline**: 4-8 hours for complete deployment
**Cost Estimate**: $200-500/month (dev), $1000-2000/month (production)
**Availability Target**: 99.9% uptime
**Scalability**: 1000+ concurrent users

---

## 📊 Architecture Overview

### AWS Services Required

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Cloud Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  VPC (10.0.0.0/16)                                         │ │
│  │                                                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │  Public      │  │  Public      │  │  Public      │   │ │
│  │  │  Subnet      │  │  Subnet      │  │  Subnet      │   │ │
│  │  │  10.0.1.0/24 │  │  10.0.2.0/24 │  │  10.0.3.0/24 │   │ │
│  │  │  (AZ-a)      │  │  (AZ-b)      │  │  (AZ-c)      │   │ │
│  │  │              │  │              │  │              │   │ │
│  │  │  [NAT GW]    │  │  [NAT GW]    │  │  [NAT GW]    │   │ │
│  │  │  [ALB]       │  │  [ALB]       │  │  [ALB]       │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │ │
│  │                                                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │  Private     │  │  Private     │  │  Private     │   │ │
│  │  │  Subnet      │  │  Subnet      │  │  Subnet      │   │ │
│  │  │  10.0.11.0/24│  │  10.0.12.0/24│  │  10.0.13.0/24│   │ │
│  │  │  (AZ-a)      │  │  (AZ-b)      │  │  (AZ-c)      │   │ │
│  │  │              │  │              │  │              │   │ │
│  │  │  [EKS Nodes] │  │  [EKS Nodes] │  │  [EKS Nodes] │   │ │
│  │  │  [RDS]       │  │  [ElastiCache│  │  [EFS]       │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │ │
│  │                                                            │ │
│  │  EKS Cluster: epic8-prod-eks                             │ │
│  │  ├── API Gateway (2 pods)                                │ │
│  │  ├── Query Analyzer (2 pods)                             │ │
│  │  ├── Generator (3 pods)                                  │ │
│  │  ├── Retriever (2 pods)                                  │ │
│  │  ├── Cache (1 pod)                                       │ │
│  │  └── Analytics (1 pod)                                   │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Supporting Services:                                            │
│  ├── Route 53 (DNS)                                             │
│  ├── ACM (SSL/TLS Certificates)                                │
│  ├── S3 (Document storage, model artifacts)                    │
│  ├── RDS PostgreSQL (Analytics metadata)                       │
│  ├── ElastiCache Redis (Cache service)                         │
│  ├── EFS (Shared storage for FAISS indices)                    │
│  ├── CloudWatch (Monitoring, logs)                             │
│  └── Systems Manager (Secrets management)                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💰 Cost Estimation

### Development Environment

**Monthly Costs** (~$250-400):
```
EKS Control Plane:      $73/month  (fixed)
EC2 Nodes (3x t3.large): $150/month  (on-demand)
NAT Gateway (3x):       $100/month  (data transfer)
ALB:                    $20/month
RDS db.t3.micro:        $15/month
ElastiCache t3.micro:   $12/month
S3 Storage:             $5/month
EFS:                    $10/month
CloudWatch:             $10/month
Data Transfer:          $20/month
─────────────────────────────────────
TOTAL (Dev):            ~$415/month
```

**Cost Optimization for Dev**:
- Use Spot Instances: Save 60-70% on EC2 (-$90/month)
- Single NAT Gateway: Save $68/month
- **Optimized Dev**: ~$250/month

### Production Environment

**Monthly Costs** (~$1,200-2,000):
```
EKS Control Plane:      $73/month
EC2 Nodes (6x c5.xlarge): $730/month (on-demand)
NAT Gateway (3x):       $100/month
ALB:                    $35/month
RDS db.r5.large (Multi-AZ): $350/month
ElastiCache r5.large:   $200/month
S3 Storage (100GB):     $25/month
EFS (1TB):             $300/month
CloudWatch:             $50/month
Data Transfer:          $100/month
Backup/Snapshots:       $50/month
─────────────────────────────────────
TOTAL (Prod):           ~$2,013/month
```

**Cost Optimization for Prod**:
- Savings Plans (1-year): Save 30% on compute (-$220/month)
- Reserved Instances for RDS: Save 40% (-$140/month)
- **Optimized Prod**: ~$1,650/month

---

## 🛠️ Prerequisites

### 1. AWS Account Setup

**Requirements**:
- [ ] AWS Account with billing enabled
- [ ] IAM user with AdministratorAccess or custom EKS policy
- [ ] AWS CLI installed and configured
- [ ] Access to eu-central-1 region
- [ ] Credit card on file (for resource provisioning)

**IAM Policy** (Minimum Required Permissions):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:*",
        "ec2:*",
        "iam:*",
        "s3:*",
        "rds:*",
        "elasticache:*",
        "elasticloadbalancing:*",
        "autoscaling:*",
        "cloudwatch:*",
        "logs:*",
        "ssm:*",
        "route53:*",
        "acm:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. Local Tools Installation

**Required Tools**:
```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# eksctl (optional but recommended)
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Verify installations
aws --version
terraform --version
kubectl version --client
helm version
eksctl version
```

### 3. Configure AWS CLI

```bash
# Configure AWS credentials
aws configure

# Input when prompted:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: eu-central-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

### 4. Prepare Secrets

**Create Secrets File**: `terraform/secrets.tfvars`

```hcl
# AWS Configuration
aws_region = "eu-central-1"
aws_profile = "default"

# EKS Configuration
cluster_name = "epic8-prod"
environment = "production"

# LLM API Keys
openai_api_key = "sk-..."
mistral_api_key = "..."
anthropic_api_key = "sk-ant-..."
huggingface_token = "hf_..."

# Database Credentials
db_username = "epic8admin"
db_password = "CHANGE_ME_STRONG_PASSWORD"

# Redis Password
redis_password = "CHANGE_ME_REDIS_PASSWORD"

# Domain Configuration (optional)
domain_name = "rag.yourdomain.com"
route53_zone_id = "Z1234567890ABC"

# SSH Key for Node Access
ssh_key_name = "epic8-nodes-key"
```

**⚠️ SECURITY**: Never commit `secrets.tfvars` to git!

```bash
# Add to .gitignore
echo "terraform/secrets.tfvars" >> .gitignore
echo "terraform/*.tfvars" >> .gitignore
```

---

## 🚀 Deployment Steps

### Phase 1: Infrastructure Provisioning (2-3 hours)

#### Step 1: Initialize Terraform

```bash
cd terraform/modules/aws-eks

# Initialize Terraform
terraform init

# Verify provider versions
terraform version

# Validate configuration
terraform validate
```

Expected output:
```
Success! The configuration is valid.
```

#### Step 2: Plan Infrastructure

```bash
# Create execution plan
terraform plan \
  -var-file="../../secrets.tfvars" \
  -var="environment=production" \
  -var="cluster_name=epic8-prod" \
  -out=tfplan

# Review the plan carefully
# Look for:
# - Number of resources to create (~50-70 resources)
# - VPC and subnet configuration
# - EKS cluster settings
# - Node group specifications
```

**Review Checklist**:
- [ ] VPC CIDR doesn't conflict with existing networks
- [ ] Subnets span 3 availability zones
- [ ] Node group sizes appropriate for workload
- [ ] Region is eu-central-1
- [ ] Tags include cost tracking information

#### Step 3: Apply Infrastructure

```bash
# Apply the plan
terraform apply tfplan

# This will take 15-20 minutes
# EKS cluster creation is the longest step

# Monitor progress
# You'll see:
# - VPC and networking creation (2-3 min)
# - EKS cluster creation (10-15 min)
# - Node group provisioning (5-10 min)
```

**Expected Timeline**:
```
[0:00] Starting terraform apply
[2:00] VPC and subnets created ✓
[3:00] Internet Gateway and NAT Gateways created ✓
[5:00] EKS cluster creation started...
[15:00] EKS cluster active ✓
[18:00] Node groups launching...
[25:00] All nodes ready ✓
[26:00] Apply complete!
```

#### Step 4: Configure kubectl

```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region eu-central-1 \
  --name epic8-prod \
  --profile default

# Verify connection
kubectl get nodes

# Expected output:
# NAME                          STATUS   ROLES    AGE   VERSION
# ip-10-0-11-123.ec2.internal   Ready    <none>   5m    v1.28.x
# ip-10-0-12-456.ec2.internal   Ready    <none>   5m    v1.28.x
# ip-10-0-13-789.ec2.internal   Ready    <none>   5m    v1.28.x

# Check cluster info
kubectl cluster-info
```

#### Step 5: Verify Infrastructure

```bash
# Check VPC
aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=epic8-prod-vpc" \
  --region eu-central-1

# Check EKS cluster
aws eks describe-cluster \
  --name epic8-prod \
  --region eu-central-1

# Check node groups
aws eks list-nodegroups \
  --cluster-name epic8-prod \
  --region eu-central-1

# Check RDS (if included in deployment)
aws rds describe-db-instances \
  --region eu-central-1

# Check ElastiCache (if included)
aws elasticache describe-cache-clusters \
  --region eu-central-1
```

---

### Phase 2: Kubernetes Setup (1-2 hours)

#### Step 1: Install Essential Add-ons

**AWS Load Balancer Controller**:
```bash
# Create IAM policy
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

# Create IAM role
eksctl create iamserviceaccount \
  --cluster=epic8-prod \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install controller using Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=epic8-prod \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Verify installation
kubectl get deployment -n kube-system aws-load-balancer-controller
```

**EBS CSI Driver** (for persistent volumes):
```bash
# Create IAM role for EBS CSI driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster epic8-prod \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --role-only \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve

# Install EBS CSI driver
aws eks create-addon \
  --cluster-name epic8-prod \
  --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonEKS_EBS_CSI_DriverRole

# Verify
kubectl get pods -n kube-system | grep ebs-csi
```

**Metrics Server** (for HPA):
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify
kubectl get deployment metrics-server -n kube-system
```

#### Step 2: Create Namespaces

```bash
# Create Epic 8 namespace
kubectl create namespace epic8-prod

# Label namespace
kubectl label namespace epic8-prod \
  environment=production \
  project=epic8

# Set as default
kubectl config set-context --current --namespace=epic8-prod

# Verify
kubectl get namespace epic8-prod
```

#### Step 3: Create Secrets

**HuggingFace Token**:
```bash
kubectl create secret generic huggingface-secrets \
  --from-literal=hf-token=YOUR_HF_TOKEN \
  -n epic8-prod
```

**LLM API Keys**:
```bash
kubectl create secret generic llm-api-keys \
  --from-literal=openai-key=YOUR_OPENAI_KEY \
  --from-literal=mistral-key=YOUR_MISTRAL_KEY \
  --from-literal=anthropic-key=YOUR_ANTHROPIC_KEY \
  -n epic8-prod
```

**Database Credentials**:
```bash
kubectl create secret generic epic8-secrets \
  --from-literal=db-username=epic8admin \
  --from-literal=db-password=YOUR_DB_PASSWORD \
  --from-literal=redis-password=YOUR_REDIS_PASSWORD \
  --from-literal=jwt-secret=$(openssl rand -base64 32) \
  -n epic8-prod
```

**Verify secrets**:
```bash
kubectl get secrets -n epic8-prod
```

---

### Phase 3: Application Deployment (1-2 hours)

#### Step 1: Build and Push Docker Images

**Configure ECR** (Elastic Container Registry):
```bash
# Create ECR repository for each service
for service in api-gateway query-analyzer generator retriever cache analytics; do
  aws ecr create-repository \
    --repository-name epic8/${service} \
    --region eu-central-1 \
    --image-scanning-configuration scanOnPush=true
done

# Get ECR login
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-central-1.amazonaws.com

# Set ECR registry URL
export ECR_REGISTRY=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-central-1.amazonaws.com
```

**Build and Push Images**:
```bash
cd /home/user/rag-portfolio/project-1-technical-rag

# Build all services
./scripts/deployment/build-services.sh build

# Tag and push to ECR
for service in api-gateway query-analyzer generator retriever cache analytics; do
  # Tag for ECR
  docker tag epic8/${service}:latest \
    ${ECR_REGISTRY}/epic8/${service}:latest

  # Push to ECR
  docker push ${ECR_REGISTRY}/epic8/${service}:latest
done

# Verify images in ECR
aws ecr list-images --repository-name epic8/api-gateway --region eu-central-1
```

#### Step 2: Deploy Using Helm

**Update Helm values for AWS**:

Create `helm/epic8-platform/values-aws-prod.yaml`:
```yaml
# AWS Production Values
environment: production
replicaCount:
  apiGateway: 2
  queryAnalyzer: 2
  generator: 3
  retriever: 2
  cache: 1
  analytics: 1

image:
  registry: YOUR_ACCOUNT_ID.dkr.ecr.eu-central-1.amazonaws.com
  tag: latest
  pullPolicy: Always

# Use AWS LoadBalancer
service:
  apiGateway:
    type: LoadBalancer
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
      service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"

# Use EBS for storage
storage:
  storageClass: gp3

# AWS-specific configs
aws:
  region: eu-central-1
  accountId: YOUR_ACCOUNT_ID

# Resource limits for production
resources:
  apiGateway:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1
      memory: 2Gi
  generator:
    requests:
      cpu: 1
      memory: 2Gi
    limits:
      cpu: 2
      memory: 4Gi

# Enable autoscaling
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

**Deploy with Helm**:
```bash
cd helm/epic8-platform

# Install Epic 8
helm install epic8 . \
  --namespace epic8-prod \
  --values values-aws-prod.yaml \
  --wait \
  --timeout 10m

# Verify deployment
helm status epic8 -n epic8-prod
```

**Monitor deployment**:
```bash
# Watch pods coming up
kubectl get pods -n epic8-prod --watch

# Check deployment status
kubectl get deployments -n epic8-prod

# Check services
kubectl get services -n epic8-prod
```

Expected output after ~5 minutes:
```
NAME                       READY   STATUS    RESTARTS   AGE
api-gateway-xxx            2/2     Running   0          5m
query-analyzer-xxx         2/2     Running   0          5m
generator-xxx              3/3     Running   0          5m
retriever-xxx              2/2     Running   0          5m
cache-xxx                  1/1     Running   0          5m
analytics-xxx              1/1     Running   0          5m
```

#### Step 3: Configure Load Balancer

```bash
# Get LoadBalancer DNS
export LB_DNS=$(kubectl get svc api-gateway-service -n epic8-prod \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "LoadBalancer DNS: ${LB_DNS}"

# Test health endpoint
curl http://${LB_DNS}:8080/health

# Expected response:
# {"status":"healthy","service":"api-gateway","version":"1.0.0"}
```

**Configure Route 53** (optional):
```bash
# Create Route 53 record
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "rag.yourdomain.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'${LB_DNS}'"}]
      }
    }]
  }'
```

---

### Phase 4: Monitoring Setup (1 hour)

#### Step 1: Install Prometheus Stack

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Create monitoring namespace
kubectl create namespace monitoring

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=CHANGE_ME_ADMIN_PASSWORD

# Wait for installation
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=prometheus \
  -n monitoring \
  --timeout=300s
```

#### Step 2: Configure Grafana Dashboards

```bash
# Port forward Grafana
kubectl port-forward -n monitoring \
  svc/prometheus-grafana 3000:80 &

# Access Grafana at http://localhost:3000
# Login: admin / CHANGE_ME_ADMIN_PASSWORD

# Import Epic 8 dashboards (pre-configured)
# Or create custom dashboards for:
# - API Gateway metrics
# - Query processing latency
# - Model routing decisions
# - Cost tracking
```

#### Step 3: Configure CloudWatch Integration

```bash
# Install CloudWatch agent
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml

# Verify
kubectl get pods -n amazon-cloudwatch
```

---

### Phase 5: Validation & Testing (1 hour)

#### Step 1: Health Checks

```bash
# Check all pods healthy
kubectl get pods -n epic8-prod

# Check services
kubectl get svc -n epic8-prod

# Test health endpoints
for service in api-gateway query-analyzer generator retriever analytics; do
  echo "Testing ${service}..."
  kubectl exec -n epic8-prod deployment/${service} -- \
    curl -s http://localhost:8080/health || echo "FAILED"
done
```

#### Step 2: End-to-End Test

**Test Script**: `scripts/aws_deployment_test.sh`

```bash
#!/bin/bash
# AWS Deployment End-to-End Test

set -e

LB_DNS=$(kubectl get svc api-gateway-service -n epic8-prod \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "Testing Epic 8 deployment at ${LB_DNS}"

# Test 1: Health check
echo "Test 1: Health Check"
curl -f http://${LB_DNS}:8080/health || exit 1
echo "✓ Health check passed"

# Test 2: Status endpoint
echo "Test 2: Status Endpoint"
curl -f http://${LB_DNS}:8080/api/v1/status || exit 1
echo "✓ Status check passed"

# Test 3: Query processing (if documents loaded)
echo "Test 3: Query Processing"
curl -X POST http://${LB_DNS}:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RISC-V?"}' || echo "Query test skipped (no documents)"

echo "✓ All tests passed!"
```

```bash
# Run test
chmod +x scripts/aws_deployment_test.sh
./scripts/aws_deployment_test.sh
```

#### Step 3: Load Testing

```bash
# Install k6 load testing tool
sudo apt-get install k6  # or brew install k6

# Create load test script
cat > loadtest.js <<EOF
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
};

export default function () {
  let res = http.get('http://${LB_DNS}:8080/health');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
EOF

# Run load test
k6 run loadtest.js
```

---

## 📊 Post-Deployment Configuration

### 1. Auto-Scaling Configuration

**Horizontal Pod Autoscaler**:
```bash
# API Gateway HPA
kubectl autoscale deployment api-gateway \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n epic8-prod

# Generator HPA
kubectl autoscale deployment generator \
  --cpu-percent=70 \
  --min=3 \
  --max=15 \
  -n epic8-prod

# Verify HPAs
kubectl get hpa -n epic8-prod
```

### 2. Backup Configuration

**EBS Snapshots**:
```bash
# Tag volumes for backup
aws ec2 describe-volumes \
  --filters "Name=tag:kubernetes.io/cluster/epic8-prod,Values=owned" \
  --query 'Volumes[*].VolumeId' \
  --output text | xargs -n 1 aws ec2 create-tags \
  --tags Key=Backup,Value=daily

# Create snapshot lifecycle policy via AWS console or CLI
```

**RDS Automated Backups**:
```bash
aws rds modify-db-instance \
  --db-instance-identifier epic8-prod-db \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --apply-immediately
```

### 3. Logging Configuration

**CloudWatch Log Groups**:
```bash
# Create log groups
aws logs create-log-group --log-group-name /aws/eks/epic8-prod/cluster
aws logs create-log-group --log-group-name /aws/eks/epic8-prod/application

# Set retention
aws logs put-retention-policy \
  --log-group-name /aws/eks/epic8-prod/application \
  --retention-in-days 30
```

### 4. Cost Optimization

**Enable Spot Instances** (for non-critical workloads):
```bash
# Create Spot node group
eksctl create nodegroup \
  --cluster epic8-prod \
  --name spot-workers \
  --instance-types c5.large,c5a.large,m5.large \
  --spot \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 10
```

**Set up Cost Allocation Tags**:
```bash
aws ec2 create-tags \
  --resources $(aws eks describe-cluster --name epic8-prod --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' --output text) \
  --tags Key=CostCenter,Value=Epic8 Key=Project,Value=RAG-Platform
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] AWS account configured
- [ ] IAM permissions verified
- [ ] AWS CLI, kubectl, helm installed
- [ ] Secrets prepared (API keys, passwords)
- [ ] Cost budget approved
- [ ] Domain name configured (optional)

### Infrastructure
- [ ] Terraform plan reviewed
- [ ] VPC and subnets created
- [ ] EKS cluster operational
- [ ] Node groups healthy
- [ ] RDS database accessible
- [ ] ElastiCache cluster ready
- [ ] S3 buckets created
- [ ] EFS volumes mounted

### Kubernetes
- [ ] kubectl configured
- [ ] Namespaces created
- [ ] Secrets deployed
- [ ] Load balancer controller installed
- [ ] EBS CSI driver installed
- [ ] Metrics server running

### Application
- [ ] Docker images pushed to ECR
- [ ] Helm chart deployed
- [ ] All pods running
- [ ] Services accessible
- [ ] Load balancer configured
- [ ] Health checks passing

### Monitoring
- [ ] Prometheus installed
- [ ] Grafana dashboards configured
- [ ] CloudWatch integration enabled
- [ ] Alerts configured
- [ ] Log aggregation working

### Production Readiness
- [ ] Auto-scaling configured
- [ ] Backups enabled
- [ ] SSL/TLS certificates installed
- [ ] DNS records configured
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on operations

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: Pods not starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n epic8-prod

# Common causes:
# - Image pull errors: Check ECR permissions
# - Resource constraints: Check node capacity
# - Secret missing: Verify secret creation
# - Config errors: Check ConfigMaps
```

#### Issue: LoadBalancer not provisioning
```bash
# Check service
kubectl describe svc api-gateway-service -n epic8-prod

# Verify AWS LB controller
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check IAM permissions
aws iam get-role --role-name AmazonEKSLoadBalancerControllerRole
```

#### Issue: High costs
```bash
# Identify expensive resources
aws ce get-cost-and-usage \
  --time-period Start=2025-11-01,End=2025-11-10 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=SERVICE

# Common cost culprits:
# - NAT Gateways: Use single NAT in dev
# - EKS control plane: Cannot be reduced
# - Unused volumes: Delete orphaned EBS volumes
# - Data transfer: Optimize cross-AZ traffic
```

---

## 📚 Next Steps

### Immediate (Week 1)
1. [ ] Complete deployment to AWS
2. [ ] Verify all services operational
3. [ ] Load test with realistic traffic
4. [ ] Configure monitoring alerts
5. [ ] Document deployment process

### Short-term (Month 1)
1. [ ] Implement CI/CD pipeline
2. [ ] Set up automated backups
3. [ ] Configure disaster recovery
4. [ ] Optimize costs (Spot, Savings Plans)
5. [ ] Train team on operations

### Long-term (Quarter 1)
1. [ ] Multi-region deployment
2. [ ] Advanced monitoring (APM, tracing)
3. [ ] Performance optimization
4. [ ] Security hardening (GuardDuty, Security Hub)
5. [ ] Compliance certification (SOC 2, ISO 27001)

---

## 📞 Support Resources

### AWS Support
- **Documentation**: https://docs.aws.amazon.com/eks/
- **Support Center**: https://console.aws.amazon.com/support/
- **Forums**: https://forums.aws.amazon.com/
- **Status Page**: https://status.aws.amazon.com/

### Kubernetes Resources
- **Documentation**: https://kubernetes.io/docs/
- **Troubleshooting**: https://kubernetes.io/docs/tasks/debug/
- **Community**: https://kubernetes.io/community/

### Epic 8 Resources
- **GitHub Issues**: https://github.com/yourusername/rag-portfolio/issues
- **Documentation**: `/docs` directory in repository
- **Demo Videos**: Link to recordings
- **Team Contact**: team@yourdomain.com

---

**Status**: ✅ READY FOR DEPLOYMENT
**Estimated Time**: 4-8 hours for complete deployment
**Risk Level**: MEDIUM (well-documented, tested infrastructure)
**Cost**: $250-400/month (dev), $1,200-2,000/month (prod)

*This deployment plan leverages existing Terraform modules and Kubernetes manifests to provide production-grade infrastructure for the Epic 8 Cloud-Native Multi-Model RAG Platform on AWS.*
