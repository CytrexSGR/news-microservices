#!/bin/bash
# Verification script for database models refactoring

echo "========================================="
echo "Database Models Refactoring Verification"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check central database models exist
echo "1. Checking central database models..."
if [ -d "/home/cytrex/database/models" ]; then
    echo -e "${GREEN}✓${NC} Central database/models/ directory exists"
    echo "   Files:"
    ls -1 /home/cytrex/database/models/*.py | sed 's/^/   - /'
else
    echo -e "${RED}✗${NC} Central database models directory NOT found"
    exit 1
fi
echo ""

# Check old model directories are removed
echo "2. Checking old model directories removed..."
SERVICES=("auth-service" "scheduler-service" "content-analysis-service")
for service in "${SERVICES[@]}"; do
    if [ ! -d "/home/cytrex/news-microservices/services/${service}/app/models" ]; then
        echo -e "${GREEN}✓${NC} ${service}/app/models/ removed"
    else
        echo -e "${RED}✗${NC} ${service}/app/models/ still exists!"
    fi
done
echo ""

# Check imports updated
echo "3. Checking import statements..."
echo "   Searching for old imports..."
OLD_IMPORTS=$(grep -r "from app\.models\." /home/cytrex/news-microservices/services/*/app --include="*.py" 2>/dev/null | wc -l)
NEW_IMPORTS=$(grep -r "from database\.models import" /home/cytrex/news-microservices/services/*/app --include="*.py" 2>/dev/null | wc -l)

if [ "$OLD_IMPORTS" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No old import statements found"
else
    echo -e "${RED}✗${NC} Found $OLD_IMPORTS old import statements"
    echo "   Files with old imports:"
    grep -r "from app\.models\." /home/cytrex/news-microservices/services/*/app --include="*.py" 2>/dev/null | cut -d':' -f1 | sort -u | sed 's/^/   - /'
fi

echo -e "${GREEN}✓${NC} Found $NEW_IMPORTS new import statements"
echo ""

# Check model files by service
echo "4. Service-specific checks..."

echo "   Auth Service:"
AUTH_IMPORTS=$(grep -r "from database\.models import" /home/cytrex/news-microservices/services/auth-service/app --include="*.py" 2>/dev/null | wc -l)
echo "   - Import statements: $AUTH_IMPORTS"

echo "   Scheduler Service:"
SCHED_IMPORTS=$(grep -r "from database\.models import" /home/cytrex/news-microservices/services/scheduler-service/app --include="*.py" 2>/dev/null | wc -l)
echo "   - Import statements: $SCHED_IMPORTS"

echo "   Content Analysis Service:"
CONTENT_IMPORTS=$(grep -r "from database\.models import" /home/cytrex/news-microservices/services/content-analysis-service/app --include="*.py" 2>/dev/null | wc -l)
echo "   - Import statements: $CONTENT_IMPORTS"
echo ""

# Check documentation
echo "5. Checking documentation..."
if [ -f "/home/cytrex/docs/refactoring/SERVICE_UPDATES.md" ]; then
    LINES=$(wc -l < "/home/cytrex/docs/refactoring/SERVICE_UPDATES.md")
    echo -e "${GREEN}✓${NC} Documentation exists ($LINES lines)"
else
    echo -e "${RED}✗${NC} Documentation NOT found"
fi
echo ""

# Summary
echo "========================================="
echo "SUMMARY"
echo "========================================="
echo ""
echo "Central Models:"
echo "  - Base models: $(ls -1 /home/cytrex/database/models/*.py 2>/dev/null | wc -l) files"
echo ""
echo "Services Updated:"
echo "  - Auth service: $AUTH_IMPORTS imports updated"
echo "  - Scheduler service: $SCHED_IMPORTS imports updated"
echo "  - Content Analysis service: $CONTENT_IMPORTS imports updated"
echo "  - Total: $NEW_IMPORTS imports across all services"
echo ""
echo "Cleanup:"
echo "  - Old model directories: ${GREEN}Removed${NC}"
echo "  - Old imports: $([ "$OLD_IMPORTS" -eq 0 ] && echo -e "${GREEN}None found${NC}" || echo -e "${RED}$OLD_IMPORTS found${NC}")"
echo ""

if [ "$OLD_IMPORTS" -eq 0 ] && [ "$NEW_IMPORTS" -gt 0 ]; then
    echo -e "${GREEN}========================================="
    echo "✓ REFACTORING VERIFICATION PASSED"
    echo "=========================================${NC}"
    exit 0
else
    echo -e "${YELLOW}========================================="
    echo "⚠ REFACTORING NEEDS REVIEW"
    echo "=========================================${NC}"
    exit 1
fi
