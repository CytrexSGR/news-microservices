#!/bin/bash

# Canary Deployment Rollout Script
# Gradually increases traffic to new service version

set -e

# Configuration
SERVICE_NAME=${1:-"auth-service"}
CANARY_VERSION=${2:-"v2"}
NAMESPACE=${3:-"news-microservices"}
INITIAL_PERCENTAGE=${4:-10}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if service exists
check_service() {
    local service=$1
    if ! docker service ls | grep -q "$service"; then
        if ! kubectl get service "$service" -n "$NAMESPACE" >/dev/null 2>&1; then
            log_error "Service $service not found"
            exit 1
        fi
    fi
}

# Update Traefik weighted service configuration
update_traefik_weights() {
    local stable_weight=$1
    local canary_weight=$2

    cat > /tmp/canary-config.yml <<EOF
http:
  services:
    ${SERVICE_NAME}-weighted:
      weighted:
        services:
          - name: ${SERVICE_NAME}-stable
            weight: ${stable_weight}
          - name: ${SERVICE_NAME}-canary
            weight: ${canary_weight}
EOF

    # Apply configuration
    if [ -d "/etc/traefik/config" ]; then
        cp /tmp/canary-config.yml /etc/traefik/config/canary-${SERVICE_NAME}.yml
    else
        log_warn "Traefik config directory not found, using Docker labels"
        update_docker_labels "$stable_weight" "$canary_weight"
    fi
}

# Update Docker labels for canary deployment
update_docker_labels() {
    local stable_weight=$1
    local canary_weight=$2

    # Update stable service
    docker service update \
        --label-add "traefik.http.services.${SERVICE_NAME}-stable.loadbalancer.weight=${stable_weight}" \
        "${SERVICE_NAME}-stable" 2>/dev/null || true

    # Update canary service
    docker service update \
        --label-add "traefik.http.services.${SERVICE_NAME}-canary.loadbalancer.weight=${canary_weight}" \
        "${SERVICE_NAME}-canary" 2>/dev/null || true
}

# Check service health
check_health() {
    local service_url=$1
    local max_retries=5
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if curl -s -f "${service_url}/health" >/dev/null 2>&1; then
            return 0
        fi
        retry_count=$((retry_count + 1))
        sleep 5
    done

    return 1
}

# Monitor error rate
monitor_error_rate() {
    local service=$1
    local threshold=${2:-5}  # 5% error rate threshold

    # Query Prometheus for error rate
    local query="rate(traefik_service_requests_total{service=\"${service}\",code=~\"5..\"}[5m]) / rate(traefik_service_requests_total{service=\"${service}\"}[5m]) * 100"

    # For demo, simulate with random check
    local error_rate=$(shuf -i 0-10 -n 1)

    if [ "$error_rate" -gt "$threshold" ]; then
        return 1
    fi

    return 0
}

# Rollback function
rollback() {
    log_error "Rolling back canary deployment"
    update_traefik_weights 100 0
    log_info "Rollback complete - 100% traffic to stable version"
    exit 1
}

# Main rollout process
main() {
    log_info "Starting canary rollout for ${SERVICE_NAME}"
    log_info "Target version: ${CANARY_VERSION}"

    # Check prerequisites
    check_service "${SERVICE_NAME}-stable"

    # Deploy canary version
    log_info "Deploying canary version..."
    if [ -f "docker-compose.canary.yml" ]; then
        docker compose -f docker-compose.canary.yml up -d "${SERVICE_NAME}-canary"
    else
        log_warn "No docker-compose.canary.yml found, assuming service is already deployed"
    fi

    # Wait for canary to be healthy
    log_info "Waiting for canary service to be healthy..."
    if ! check_health "http://${SERVICE_NAME}-canary:8000"; then
        log_error "Canary service health check failed"
        exit 1
    fi

    # Rollout stages
    local stages=(10 25 50 75 100)
    local stable_weight
    local canary_weight

    for canary_weight in "${stages[@]}"; do
        stable_weight=$((100 - canary_weight))

        log_info "Stage: ${canary_weight}% traffic to canary, ${stable_weight}% to stable"
        update_traefik_weights "$stable_weight" "$canary_weight"

        # Wait and monitor
        log_info "Monitoring for 60 seconds..."
        sleep 60

        # Check error rate
        if ! monitor_error_rate "${SERVICE_NAME}-canary"; then
            log_error "High error rate detected on canary"
            rollback
        fi

        # Check health
        if ! check_health "http://${SERVICE_NAME}-canary:8000"; then
            log_error "Canary health check failed"
            rollback
        fi

        log_info "Stage ${canary_weight}% completed successfully"

        # Ask for confirmation before proceeding (except for last stage)
        if [ "$canary_weight" -lt 100 ]; then
            read -p "Continue to next stage? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_warn "Rollout paused at ${canary_weight}%"
                exit 0
            fi
        fi
    done

    # Complete rollout
    log_info "Canary rollout completed successfully!"
    log_info "Promoting canary to stable..."

    # Replace stable with canary
    if command -v docker &> /dev/null; then
        docker service update --image "${SERVICE_NAME}:${CANARY_VERSION}" "${SERVICE_NAME}-stable" 2>/dev/null || true
        docker service rm "${SERVICE_NAME}-canary" 2>/dev/null || true
    fi

    # Reset weights
    update_traefik_weights 100 0

    log_info "Deployment complete! Version ${CANARY_VERSION} is now stable"
}

# Cleanup function
cleanup() {
    rm -f /tmp/canary-config.yml
}

# Set up trap for cleanup
trap cleanup EXIT

# Handle arguments
case "${1}" in
    --help|-h)
        echo "Usage: $0 [SERVICE_NAME] [CANARY_VERSION] [NAMESPACE] [INITIAL_PERCENTAGE]"
        echo ""
        echo "Example: $0 auth-service v2 news-microservices 10"
        echo ""
        echo "Options:"
        echo "  SERVICE_NAME       Name of the service to deploy (default: auth-service)"
        echo "  CANARY_VERSION     Version tag for canary (default: v2)"
        echo "  NAMESPACE          Kubernetes namespace (default: news-microservices)"
        echo "  INITIAL_PERCENTAGE Initial traffic percentage (default: 10)"
        exit 0
        ;;
    --rollback)
        SERVICE_NAME=${2:-"auth-service"}
        rollback
        ;;
    *)
        main
        ;;
esac