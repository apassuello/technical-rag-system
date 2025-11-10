#!/bin/bash
# Epic 8 Demo Script - 5-10 Minute Demo
# Author: [Your Name]
# Date: $(date +%Y-%m-%d)

set -e  # Exit on error

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Epic 8: Cloud-Native Multi-Model RAG Platform"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Demonstrating:"
echo "  • Microservices architecture (6 independent services)"
echo "  • Intelligent model routing (Epic 1 integration)"
echo "  • Cost-optimized cloud deployment ($3.20/day)"
echo ""
printf "${YELLOW}Press Enter to continue...${NC}"
read

# =============================================================================
# Part 1: Architecture Overview
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Part 1: Architecture Overview"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "6 Independent Microservices:"
echo ""
echo "  1. API Gateway      - Request routing and orchestration"
echo "  2. Query Analyzer   - Epic 1 complexity classification"
echo "  3. Generator        - Epic 1 multi-model answer generation"
echo "  4. Retriever        - Epic 2 advanced retrieval"
echo "  5. Analytics        - Metrics and cost tracking"
echo "  6. Cache (Redis)    - Performance optimization"
echo ""
echo "Architecture:"
echo ""
echo "  Client → API Gateway → Query Analyzer → Generator"
echo "                             ↓              ↓"
echo "                        Analytics ← Retriever"
echo ""
printf "${YELLOW}Press Enter to start services...${NC}"
read

# =============================================================================
# Part 2: Start Services
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Part 2: Starting Services (Docker Compose)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "${BLUE}Starting all services in background...${NC}\n"
docker-compose up -d

echo ""
printf "${YELLOW}Waiting for services to be ready (10 seconds)...${NC}\n"
sleep 10

# =============================================================================
# Part 3: Health Checks
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Part 3: Verifying All Services Healthy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check each service
SERVICES=(
  "8000:API Gateway"
  "8001:Query Analyzer"
  "8002:Generator"
  "8003:Analytics"
  "8004:Retriever"
)

for service in "${SERVICES[@]}"; do
  PORT="${service%%:*}"
  NAME="${service##*:}"

  if curl -s http://localhost:${PORT}/health > /dev/null 2>&1; then
    STATUS=$(curl -s http://localhost:${PORT}/health | jq -r '.status // "unknown"')
    printf "  ${GREEN}✓${NC} Port $PORT: $NAME (${GREEN}$STATUS${NC})\n"
  else
    printf "  ${RED}✗${NC} Port $PORT: $NAME (${RED}not responding${NC})\n"
  fi
done

echo ""
printf "${YELLOW}Press Enter to send queries...${NC}"
read

# =============================================================================
# Part 4: Simple Query Test
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Part 4: Testing Simple Query"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "${BLUE}Query:${NC} 'What is Python?'\n"
printf "${YELLOW}Expected:${NC} Should use Ollama (FREE model)\n"
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}' || echo '{"error": "Service unavailable"}')

if echo "$RESPONSE" | jq -e . >/dev/null 2>&1; then
  MODEL=$(echo "$RESPONSE" | jq -r '.metadata.model_used // "unknown"')
  COST=$(echo "$RESPONSE" | jq -r '.metadata.cost // 0')
  ANSWER=$(echo "$RESPONSE" | jq -r '.answer // "No answer"' | head -c 150)

  printf "${GREEN}Response:${NC}\n"
  printf "  Model: ${BLUE}$MODEL${NC}\n"
  printf "  Cost: ${GREEN}\$$COST${NC}\n"
  printf "  Answer: \"$ANSWER...\"\n"
else
  printf "${RED}Error: Could not process query${NC}\n"
  echo "$RESPONSE"
fi

echo ""
printf "${YELLOW}Press Enter to send complex query...${NC}"
read

# =============================================================================
# Part 5: Complex Query Test
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Part 5: Testing Complex Query"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "${BLUE}Query:${NC} 'Comprehensive analysis of distributed systems...'\n"
printf "${YELLOW}Expected:${NC} Should use GPT-OSS or Mistral (advanced model)\n"
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Provide a comprehensive analysis of distributed consensus protocols including Raft and Paxos, with implications for CAP theorem"}' || echo '{"error": "Service unavailable"}')

if echo "$RESPONSE" | jq -e . >/dev/null 2>&1; then
  MODEL=$(echo "$RESPONSE" | jq -r '.metadata.model_used // "unknown"')
  COST=$(echo "$RESPONSE" | jq -r '.metadata.cost // 0')
  ANSWER=$(echo "$RESPONSE" | jq -r '.answer // "No answer"' | head -c 150)

  printf "${GREEN}Response:${NC}\n"
  printf "  Model: ${BLUE}$MODEL${NC}\n"
  printf "  Cost: ${GREEN}\$$COST${NC}\n"
  printf "  Answer: \"$ANSWER...\"\n"
else
  printf "${RED}Error: Could not process query${NC}\n"
  echo "$RESPONSE"
fi

echo ""
printf "${YELLOW}Press Enter to view metrics...${NC}"
read

# =============================================================================
# Part 6: System Metrics
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Part 6: System Metrics & Analytics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

METRICS=$(curl -s http://localhost:8003/metrics || echo '{}')

if echo "$METRICS" | jq -e . >/dev/null 2>&1; then
  TOTAL_QUERIES=$(echo "$METRICS" | jq -r '.total_queries // 0')
  AVG_LATENCY=$(echo "$METRICS" | jq -r '.average_latency // 0')
  TOTAL_COST=$(echo "$METRICS" | jq -r '.total_cost // 0')

  printf "${GREEN}System Metrics:${NC}\n"
  printf "  Total Queries: ${BLUE}$TOTAL_QUERIES${NC}\n"
  printf "  Average Latency: ${BLUE}$AVG_LATENCY ms${NC}\n"
  printf "  Total Cost: ${GREEN}\$$TOTAL_COST${NC}\n"

  if echo "$METRICS" | jq -e '.model_distribution' >/dev/null 2>&1; then
    echo ""
    printf "${GREEN}Model Distribution:${NC}\n"
    echo "$METRICS" | jq -r '.model_distribution | to_entries | .[] | "  \(.key): \(.value)"'
  fi
else
  printf "${RED}Error: Could not fetch metrics${NC}\n"
fi

echo ""
printf "${YELLOW}Press Enter to demonstrate scaling...${NC}"
read

# =============================================================================
# Part 7: Scaling Demo
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Part 7: Demonstrating Service Scaling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "${BLUE}Scaling Generator service from 1 to 3 instances...${NC}\n"
docker-compose up -d --scale generator=3 --no-recreate

echo ""
printf "${YELLOW}Waiting for scale-up...${NC}\n"
sleep 5

echo ""
printf "${GREEN}Current generator instances:${NC}\n"
docker-compose ps generator | tail -n +2 | nl

echo ""
echo "Benefit: Load balancing across 3 instances for high availability"
echo ""
printf "${YELLOW}Press Enter to view deployment options...${NC}"
read

# =============================================================================
# Part 8: Cloud Deployment
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Part 8: Cloud Deployment Options"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "${BLUE}Local (Docker Compose):${NC}\n"
echo "  Cost: FREE"
echo "  Use Case: Development, testing"
echo "  Setup: docker-compose up"
echo ""
printf "${BLUE}AWS ECS Fargate (RECOMMENDED):${NC}\n"
echo "  Cost: $3.20/day = 31 days on $100 budget"
echo "  Use Case: Production demos, portfolio"
echo "  Setup: ./deployment/ecs/deploy.sh setup && build && deploy"
echo ""
printf "${BLUE}AWS EKS (Full Kubernetes):${NC}\n"
echo "  Cost: $120+/month"
echo "  Use Case: Enterprise production with advanced features"
echo "  Setup: terraform apply + helm install"
echo ""
echo "Key Advantage: ECS Fargate is 88% cheaper than GPU-based approach"
echo "               while maintaining production-grade capabilities"
echo ""
printf "${YELLOW}Press Enter to finish...${NC}"
read

# =============================================================================
# Cleanup
# =============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Demo Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "${YELLOW}Stopping services...${NC}\n"
docker-compose down

echo ""
echo "═══════════════════════════════════════════════════════════"
printf "${GREEN}Key Achievements:${NC}\n"
echo "  • 6-service microservices architecture"
echo "  • Independent scaling and deployment"
echo "  • Intelligent model routing (99.5% accuracy)"
echo "  • 88% cost reduction vs GPU approach"
echo "  • Production-ready with Infrastructure as Code"
echo "═══════════════════════════════════════════════════════════"
echo ""
printf "${BLUE}Next Steps:${NC}\n"
echo "  • Deploy to AWS ECS: cd deployment/ecs && ./deploy.sh"
echo "  • View architecture docs: docs/epic8/"
echo "  • Explore K8s manifests: k8s/"
echo ""
printf "${GREEN}Thank you!${NC}\n"
echo ""
