#!/bin/bash
# Docker Build Validation Script
# Prevents regression to bloated images

set -e

SERVICE=$1
MAX_SIZE_MB=${2:-600}  # Default 600 MB max per service

if [ -z "$SERVICE" ]; then
  echo "Usage: $0 <service-name> [max-size-mb]"
  echo ""
  echo "Examples:"
  echo "  $0 auth 400      # Validate auth-service, max 400 MB"
  echo "  $0 scraping 600  # Validate scraping-service, max 600 MB"
  exit 1
fi

echo "🔍 Validating docker build for $SERVICE-service..."
echo ""

# Build image
IMAGE_NAME="news-microservices-${SERVICE}-service"
SERVICE_DIR="/home/cytrex/news-microservices/services/${SERVICE}-service"

if [ ! -d "$SERVICE_DIR" ]; then
  echo "❌ ERROR: Service directory not found: $SERVICE_DIR"
  exit 1
fi

echo "📦 Building image..."
docker build -t ${IMAGE_NAME}:test "$SERVICE_DIR" > /tmp/docker-build-${SERVICE}.log 2>&1

if [ $? -ne 0 ]; then
  echo "❌ FAIL: Build failed"
  tail -50 /tmp/docker-build-${SERVICE}.log
  exit 1
fi

# Get image size in MB
SIZE_RAW=$(docker images ${IMAGE_NAME}:test --format "{{.Size}}")
if [[ "$SIZE_RAW" =~ GB ]]; then
  SIZE=$(echo "$SIZE_RAW" | sed 's/GB//' | awk '{print $1 * 1000}')
elif [[ "$SIZE_RAW" =~ MB ]]; then
  SIZE=$(echo "$SIZE_RAW" | sed 's/MB//')
else
  SIZE=0
fi

echo "📊 Image size: ${SIZE} MB (max: ${MAX_SIZE_MB} MB)"

# Check size
if (( $(echo "$SIZE > $MAX_SIZE_MB" | bc -l) )); then
  echo "❌ FAIL: Image too large (${SIZE} MB > ${MAX_SIZE_MB} MB)"
  echo ""
  echo "🔎 Analyzing layers:"
  docker history ${IMAGE_NAME}:test --no-trunc --format "table {{.Size}}\t{{.CreatedBy}}" | head -20
  echo ""
  echo "🔎 Package count:"
  PKG_COUNT=$(docker run --rm ${IMAGE_NAME}:test pip list 2>/dev/null | wc -l)
  echo "   ${PKG_COUNT} packages installed"
  echo ""
  echo "🔎 Checking for dev dependencies:"
  docker run --rm ${IMAGE_NAME}:test pip list 2>/dev/null | grep -E "pytest|black|mypy|flake8|pre-commit" || echo "   ✓ No dev deps found"
  echo ""
  echo "💡 Suggestions:"
  echo "   1. Check for duplicate package installations in Dockerfile"
  echo "   2. Ensure dev dependencies are in requirements-dev.txt"
  echo "   3. Use selective COPY (not 'COPY . .')"
  echo "   4. Verify multi-stage build is working correctly"
  exit 1
fi

# Check for dev dependencies
echo "🔍 Checking for dev dependencies..."
DEV_DEPS=$(docker run --rm ${IMAGE_NAME}:test pip list 2>/dev/null | grep -E "pytest|black|mypy|flake8|pre-commit|ipython|jupyter" | wc -l)

if [ "$DEV_DEPS" -gt 0 ]; then
  echo "❌ FAIL: Found $DEV_DEPS dev dependencies in production image!"
  docker run --rm ${IMAGE_NAME}:test pip list 2>/dev/null | grep -E "pytest|black|mypy|flake8|pre-commit|ipython|jupyter"
  echo ""
  echo "💡 Fix: Move these to requirements-dev.txt"
  exit 1
fi

echo "   ✓ No dev dependencies found"

# Check Python version consistency
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(docker run --rm ${IMAGE_NAME}:test python --version 2>&1)
if [[ ! "$PYTHON_VERSION" =~ "Python 3.11" ]]; then
  echo "⚠️  WARNING: Using $PYTHON_VERSION (expected Python 3.11.x)"
  echo "   This breaks shared base image strategy!"
fi

echo "   $PYTHON_VERSION"

# Check multi-stage build effectiveness
echo "🔍 Checking multi-stage build..."
BUILDER_LAYERS=$(docker history ${IMAGE_NAME}:test 2>/dev/null | grep -c "builder" || echo 0)
if [ "$BUILDER_LAYERS" -eq 0 ]; then
  echo "⚠️  WARNING: No builder stage found (single-stage build)"
  echo "   Multi-stage builds reduce image size by 150-200 MB"
else
  echo "   ✓ Multi-stage build detected"
fi

# Check for gcc in runtime
echo "🔍 Checking for build tools in runtime..."
HAS_GCC=$(docker run --rm ${IMAGE_NAME}:test sh -c "which gcc 2>/dev/null" | wc -l)
if [ "$HAS_GCC" -gt 0 ]; then
  echo "❌ FAIL: gcc found in runtime image"
  echo "   Build tools should only be in builder stage!"
  exit 1
fi

echo "   ✓ No build tools in runtime"

# Check for COPY . . usage
echo "🔍 Checking Dockerfile patterns..."
if grep -q "^COPY \. \." "$SERVICE_DIR/Dockerfile"; then
  echo "⚠️  WARNING: Found 'COPY . .' in Dockerfile"
  echo "   Use selective copy: COPY app/ app/"
else
  echo "   ✓ Selective COPY used"
fi

# Summary
echo ""
echo "═══════════════════════════════════════"
echo "✅ PASS: All validation checks passed!"
echo "═══════════════════════════════════════"
echo "   Size: ${SIZE} MB (< ${MAX_SIZE_MB} MB)"
echo "   No dev dependencies"
echo "   Python: $PYTHON_VERSION"
echo "   No build tools in runtime"
echo ""
echo "🎯 Image ready for deployment"

# Cleanup test image
docker rmi ${IMAGE_NAME}:test > /dev/null 2>&1 || true
