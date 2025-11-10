#!/bin/bash

# ═══════════════════════════════════════════════════════════════════
# Epic 8 Cost Monitoring Script
# ═══════════════════════════════════════════════════════════════════
#
# This script tracks AWS costs for the Epic 8 deployment and estimates
# remaining budget runway.
#
# Usage:
#   ./check-costs.sh
#
# Environment Variables:
#   AWS_REGION - AWS region (default: us-east-1)
#   BUDGET_TOTAL - Total budget in USD (default: 100)
#
# ═══════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
BUDGET_TOTAL="${BUDGET_TOTAL:-100}"
DAILY_ESTIMATE="3.20"

# Get current month dates
START_DATE=$(date -u +%Y-%m-01)
END_DATE=$(date -u +%Y-%m-%d)
TOMORROW=$(date -u -d '+1 day' +%Y-%m-%d)

echo "═══════════════════════════════════════════════════════════════"
echo "            Epic 8 AWS Cost Report"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Total Spend This Month
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}Current Month Spend${NC}"
echo "Period: $START_DATE to $END_DATE"
echo ""

TOTAL_SPENT=$(aws ce get-cost-and-usage \
  --time-period Start=$START_DATE,End=$TOMORROW \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --region us-east-1 \
  --query 'ResultsByTime[0].Total.UnblendedCost.Amount' \
  --output text 2>/dev/null || echo "0")

TOTAL_SPENT=$(printf "%.2f" $TOTAL_SPENT)

echo "  Total Spent:  \$$TOTAL_SPENT"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Cost by Service
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}Cost by Service (Last 7 Days)${NC}"
echo ""

LAST_WEEK=$(date -u -d '7 days ago' +%Y-%m-%d)

aws ce get-cost-and-usage \
  --time-period Start=$LAST_WEEK,End=$TOMORROW \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --group-by Type=SERVICE \
  --region us-east-1 \
  --query 'ResultsByTime[-1].Groups[?Metrics.UnblendedCost.Amount > `0.01`].{Service:Keys[0],Cost:Metrics.UnblendedCost.Amount}' \
  --output table 2>/dev/null || echo "  No cost data available yet"

echo ""

# ═══════════════════════════════════════════════════════════════════
# Budget Analysis
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}Budget Analysis${NC}"
echo ""

REMAINING=$(echo "$BUDGET_TOTAL - $TOTAL_SPENT" | bc)
PERCENT_USED=$(echo "scale=1; ($TOTAL_SPENT / $BUDGET_TOTAL) * 100" | bc)

echo "  Budget:       \$$BUDGET_TOTAL"
echo "  Spent:        \$$TOTAL_SPENT ($PERCENT_USED%)"
echo "  Remaining:    \$$REMAINING"
echo ""

# Alert if over 80%
if (( $(echo "$PERCENT_USED >= 80" | bc -l) )); then
    echo -e "  ${RED}⚠ WARNING: Budget is 80%+ used!${NC}"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════════
# Runtime Estimate
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}Estimated Runtime${NC}"
echo ""

# Calculate days running so far
DAYS_RUNNING=$(( ($(date -u +%s) - $(date -u -d $START_DATE +%s)) / 86400 ))

# Calculate actual daily average
if [[ "$DAYS_RUNNING" -gt 0 && $(echo "$TOTAL_SPENT > 0" | bc) -eq 1 ]]; then
    ACTUAL_DAILY=$(echo "scale=2; $TOTAL_SPENT / $DAYS_RUNNING" | bc)
else
    ACTUAL_DAILY=$DAILY_ESTIMATE
fi

# Calculate remaining days
if (( $(echo "$ACTUAL_DAILY > 0" | bc -l) )); then
    REMAINING_DAYS=$(echo "scale=0; $REMAINING / $ACTUAL_DAILY" | bc)
else
    REMAINING_DAYS="N/A"
fi

echo "  Days Running:     $DAYS_RUNNING"
echo "  Avg Daily Cost:   \$$ACTUAL_DAILY"
echo "  Estimated Daily:  \$$DAILY_ESTIMATE"
echo ""

if [[ "$REMAINING_DAYS" != "N/A" ]]; then
    END_EST=$(date -u -d "+${REMAINING_DAYS} days" +%Y-%m-%d)
    echo -e "  ${GREEN}Remaining Days:   ~$REMAINING_DAYS days${NC}"
    echo "  Budget Depletes:  ~$END_EST"
else
    echo "  Remaining Days:   Calculating..."
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# Daily Cost Trend
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}Daily Cost Trend (Last 7 Days)${NC}"
echo ""

aws ce get-cost-and-usage \
  --time-period Start=$LAST_WEEK,End=$TOMORROW \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --region us-east-1 \
  --query 'ResultsByTime[].{Date:TimePeriod.Start,Cost:Total.UnblendedCost.Amount}' \
  --output table 2>/dev/null || echo "  No cost data available yet"

echo ""

# ═══════════════════════════════════════════════════════════════════
# Cost Optimization Suggestions
# ═══════════════════════════════════════════════════════════════════

if (( $(echo "$ACTUAL_DAILY > $DAILY_ESTIMATE" | bc -l) )); then
    echo -e "${YELLOW}Cost Optimization Suggestions:${NC}"
    echo ""
    echo "  Your actual daily cost (\$$ACTUAL_DAILY) is higher than estimated (\$$DAILY_ESTIMATE)"
    echo ""
    echo "  To reduce costs:"
    echo "  1. Reduce ECS task sizes (256 CPU → 128 CPU)"
    echo "  2. Scale down to 0 during non-usage hours"
    echo "  3. Remove analytics service if not needed"
    echo "  4. Reduce log retention (7 days → 3 days)"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════════
# Quick Actions
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}Quick Actions${NC}"
echo ""
echo "  Stop all services:      aws ecs update-service --cluster epic8-ecs-cluster --service <name> --desired-count 0"
echo "  Start all services:     aws ecs update-service --cluster epic8-ecs-cluster --service <name> --desired-count 1"
echo "  View detailed costs:    aws ce get-cost-and-usage --time-period Start=$START_DATE,End=$TOMORROW --granularity DAILY --metrics UnblendedCost"
echo ""

echo "═══════════════════════════════════════════════════════════════"

# Exit with warning code if budget exceeded
if (( $(echo "$PERCENT_USED >= 100" | bc -l) )); then
    exit 2
elif (( $(echo "$PERCENT_USED >= 80" | bc -l) )); then
    exit 1
else
    exit 0
fi
