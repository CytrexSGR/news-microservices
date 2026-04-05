#!/bin/bash
#
# Frontend Validation Script
#
# Performs comprehensive validation of frontend structure and configuration
# to ensure everything is in a safe, recoverable state.
#
# Usage:
#   ./scripts/validate-frontend.sh           # Run all checks
#   ./scripts/validate-frontend.sh --fix     # Attempt to fix issues automatically
#   ./scripts/validate-frontend.sh --report  # Generate detailed report
#
# Author: Auto-generated protection measure (2025-10-21)
# Incident: Frontend Total Loss - Never again.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="/home/cytrex/news-microservices"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
FIX_MODE=false
REPORT_MODE=false

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --report)
            REPORT_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --fix       Attempt to automatically fix issues"
            echo "  --report    Generate detailed validation report"
            echo "  --help, -h  Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Print functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_check() {
    echo -n "$1... "
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    ((CHECKS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}"
    echo -e "${RED}  $1${NC}"
    ((CHECKS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING${NC}"
    echo -e "${YELLOW}  $1${NC}"
    ((CHECKS_WARNING++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_fix() {
    if [ "$FIX_MODE" = true ]; then
        echo -e "${GREEN}[FIX]${NC} $1"
    fi
}

# Validation checks

check_project_structure() {
    print_header "Project Structure Validation"

    print_check "Frontend directory exists"
    if [ -d "${FRONTEND_DIR}" ]; then
        print_pass
    else
        print_fail "Frontend directory not found at ${FRONTEND_DIR}"
        return 1
    fi

    print_check "src/ directory exists"
    if [ -d "${FRONTEND_DIR}/src" ]; then
        print_pass
    else
        print_fail "src/ directory not found"
    fi

    print_check "package.json exists"
    if [ -f "${FRONTEND_DIR}/package.json" ]; then
        print_pass
    else
        print_fail "package.json not found"
    fi

    print_check "node_modules/ exists"
    if [ -d "${FRONTEND_DIR}/node_modules" ]; then
        print_pass
    else
        print_warning "node_modules/ not found - run 'npm install'"
    fi
}

check_git_status() {
    print_header "Git Repository Validation"

    print_check "No nested .git in frontend/"
    if [ -d "${FRONTEND_DIR}/.git" ]; then
        print_fail "Nested .git directory found - CRITICAL ISSUE!"
        if [ "$FIX_MODE" = true ]; then
            print_fix "Removing nested .git directory"
            rm -rf "${FRONTEND_DIR}/.git"
        fi
    else
        print_pass
    fi

    print_check "package.json is tracked by git"
    cd "${PROJECT_ROOT}"
    if git ls-files --error-unmatch frontend/package.json &>/dev/null; then
        print_pass
    else
        print_fail "package.json is not tracked by git"
        if [ "$FIX_MODE" = true ]; then
            print_fix "Adding package.json to git"
            git add frontend/package.json
        fi
    fi

    print_check "package-lock.json is tracked by git"
    if git ls-files --error-unmatch frontend/package-lock.json &>/dev/null; then
        print_pass
    else
        print_warning "package-lock.json is not tracked by git"
        if [ "$FIX_MODE" = true ]; then
            print_fix "Adding package-lock.json to git"
            git add frontend/package-lock.json
        fi
    fi

    print_check "No uncommitted changes to package files"
    if git diff --name-only | grep -q "frontend/package"; then
        print_warning "Uncommitted changes detected in package files"
        git diff --name-only | grep "frontend/package"
    else
        print_pass
    fi
}

check_documentation() {
    print_header "Documentation Validation"

    local docs=(
        "frontend/FEATURES.md"
        "frontend/ARCHITECTURE.md"
        "frontend/SETUP.md"
        "docs/guides/FRONTEND-PROJECTS.md"
    )

    for doc in "${docs[@]}"; do
        print_check "${doc} exists"
        if [ -f "${PROJECT_ROOT}/${doc}" ]; then
            print_pass
            # Check if document has content (more than 10 lines)
            local lines=$(wc -l < "${PROJECT_ROOT}/${doc}")
            if [ "$lines" -lt 10 ]; then
                print_warning "${doc} exists but seems incomplete (${lines} lines)"
            fi
        else
            print_fail "${doc} not found"
        fi
    done
}

check_configuration() {
    print_header "Configuration Validation"

    print_check "vite.config.ts exists"
    if [ -f "${FRONTEND_DIR}/vite.config.ts" ]; then
        print_pass
    else
        print_warning "vite.config.ts not found"
    fi

    print_check "tsconfig.json exists"
    if [ -f "${FRONTEND_DIR}/tsconfig.json" ]; then
        print_pass
    else
        print_fail "tsconfig.json not found"
    fi

    print_check "tailwind.config.js exists"
    if [ -f "${FRONTEND_DIR}/tailwind.config.js" ]; then
        print_pass
    else
        print_warning "tailwind.config.js not found"
    fi

    print_check ".gitignore excludes node_modules"
    if grep -q "node_modules" "${PROJECT_ROOT}/.gitignore" 2>/dev/null; then
        print_pass
    else
        print_warning ".gitignore doesn't exclude node_modules"
    fi

    print_check ".gitignore does NOT exclude package.json"
    if grep -q "^package.json$" "${PROJECT_ROOT}/.gitignore" 2>/dev/null; then
        print_fail "package.json should NOT be in .gitignore!"
        if [ "$FIX_MODE" = true ]; then
            print_fix "Removing package.json from .gitignore"
            sed -i '/^package.json$/d' "${PROJECT_ROOT}/.gitignore"
        fi
    else
        print_pass
    fi
}

check_dependencies() {
    print_header "Dependencies Validation"

    print_check "package.json is valid JSON"
    if jq empty "${FRONTEND_DIR}/package.json" 2>/dev/null; then
        print_pass
    else
        print_fail "package.json is not valid JSON"
    fi

    print_check "package-lock.json exists"
    if [ -f "${FRONTEND_DIR}/package-lock.json" ]; then
        print_pass
    else
        print_warning "package-lock.json not found - run 'npm install'"
    fi

    # Check for critical dependencies
    local critical_deps=(
        "react"
        "react-dom"
        "vite"
        "@tanstack/react-query"
        "react-router-dom"
        "axios"
        "zustand"
    )

    for dep in "${critical_deps[@]}"; do
        print_check "Dependency '${dep}' is present"
        if grep -q "\"${dep}\"" "${FRONTEND_DIR}/package.json"; then
            print_pass
        else
            print_warning "Critical dependency '${dep}' not found in package.json"
        fi
    done
}

check_frontend_pages() {
    print_header "Frontend Pages Validation"

    local pages=(
        "src/pages/LoginPage.tsx"
        "src/pages/HomePage.tsx"
        "src/pages/FeedListPage.tsx"
        "src/pages/FeedDetailPage.tsx"
        "src/pages/DashboardListPage.tsx"
        "src/pages/DashboardDetailPage.tsx"
    )

    for page in "${pages[@]}"; do
        print_check "${page} exists"
        if [ -f "${FRONTEND_DIR}/${page}" ]; then
            print_pass
        else
            print_warning "${page} not found"
        fi
    done
}

check_protection_mechanisms() {
    print_header "Protection Mechanisms Validation"

    print_check "backup.sh script exists"
    if [ -f "${PROJECT_ROOT}/scripts/backup.sh" ]; then
        print_pass
    else
        print_warning "backup.sh script not found"
    fi

    print_check "backup.sh is executable"
    if [ -x "${PROJECT_ROOT}/scripts/backup.sh" ]; then
        print_pass
    else
        print_warning "backup.sh is not executable"
        if [ "$FIX_MODE" = true ]; then
            print_fix "Making backup.sh executable"
            chmod +x "${PROJECT_ROOT}/scripts/backup.sh"
        fi
    fi

    print_check "pre-commit hook exists"
    if [ -f "${PROJECT_ROOT}/.git/hooks/pre-commit" ]; then
        print_pass
    else
        print_warning "pre-commit hook not found"
    fi

    print_check "pre-commit hook is executable"
    if [ -x "${PROJECT_ROOT}/.git/hooks/pre-commit" ]; then
        print_pass
    else
        print_warning "pre-commit hook is not executable"
        if [ "$FIX_MODE" = true ]; then
            print_fix "Making pre-commit hook executable"
            chmod +x "${PROJECT_ROOT}/.git/hooks/pre-commit"
        fi
    fi

    print_check "Backup directory exists"
    if [ -d "/home/cytrex/backups" ]; then
        print_pass
    else
        print_warning "Backup directory not found"
        if [ "$FIX_MODE" = true ]; then
            print_fix "Creating backup directory"
            mkdir -p /home/cytrex/backups
        fi
    fi
}

generate_report() {
    if [ "$REPORT_MODE" = false ]; then
        return
    fi

    local report_file="/tmp/frontend-validation-report-$(date +%Y%m%d-%H%M%S).txt"

    {
        echo "========================================="
        echo "Frontend Validation Report"
        echo "========================================="
        echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "Summary:"
        echo "  Checks Passed: ${CHECKS_PASSED}"
        echo "  Checks Failed: ${CHECKS_FAILED}"
        echo "  Warnings: ${CHECKS_WARNING}"
        echo ""
        echo "Details:"
        echo ""

        # Project info
        echo "Project Root: ${PROJECT_ROOT}"
        echo "Frontend Directory: ${FRONTEND_DIR}"
        echo ""

        # Git status
        cd "${PROJECT_ROOT}"
        echo "Git Status:"
        git status --short | head -20
        echo ""

        # Package info
        if [ -f "${FRONTEND_DIR}/package.json" ]; then
            echo "package.json info:"
            jq '.name, .version' "${FRONTEND_DIR}/package.json"
            echo ""
        fi

        # File counts
        echo "File Counts:"
        echo "  TypeScript files: $(find "${FRONTEND_DIR}/src" -name "*.tsx" -o -name "*.ts" 2>/dev/null | wc -l)"
        echo "  Component files: $(find "${FRONTEND_DIR}/src/components" -name "*.tsx" 2>/dev/null | wc -l)"
        echo "  Page files: $(find "${FRONTEND_DIR}/src/pages" -name "*.tsx" 2>/dev/null | wc -l)"
        echo ""

    } > "${report_file}"

    print_info "Detailed report saved to: ${report_file}"
}

# Main execution
main() {
    print_header "Frontend Validation"
    echo -e "${BLUE}Timestamp: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    if [ "$FIX_MODE" = true ]; then
        echo -e "${YELLOW}FIX MODE ENABLED${NC}"
    fi
    echo ""

    # Run all checks
    check_project_structure
    echo ""
    check_git_status
    echo ""
    check_documentation
    echo ""
    check_configuration
    echo ""
    check_dependencies
    echo ""
    check_frontend_pages
    echo ""
    check_protection_mechanisms
    echo ""

    # Generate report if requested
    generate_report

    # Final summary
    print_header "Validation Summary"
    echo -e "${GREEN}Checks Passed: ${CHECKS_PASSED}${NC}"
    echo -e "${RED}Checks Failed: ${CHECKS_FAILED}${NC}"
    echo -e "${YELLOW}Warnings: ${CHECKS_WARNING}${NC}"
    echo ""

    if [ ${CHECKS_FAILED} -eq 0 ]; then
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Frontend validation successful!${NC}"
        echo -e "${GREEN}========================================${NC}"
        exit 0
    else
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}Frontend validation failed!${NC}"
        echo -e "${RED}========================================${NC}"
        echo ""
        echo "Please fix the issues above."
        if [ "$FIX_MODE" = false ]; then
            echo "You can run with --fix to attempt automatic fixes:"
            echo "  ./scripts/validate-frontend.sh --fix"
        fi
        exit 1
    fi
}

# Run main
main
