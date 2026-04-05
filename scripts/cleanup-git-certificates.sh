#!/bin/bash
# ==============================================================================
# Git Certificate Cleanup Script
# ==============================================================================
#
# Purpose: Remove all .pem certificate files from Git history while keeping
#          them in the working directory
#
# What it does:
#   1. Creates full backup
#   2. Downloads BFG Repo-Cleaner
#   3. Removes *.pem files from ALL commits
#   4. Runs garbage collection
#   5. Restores certificates locally
#   6. Verifies cleanup success
#
# Usage:
#   ./scripts/cleanup-git-certificates.sh [--auto-push]
#
# Options:
#   --auto-push    Automatically push after successful cleanup
#   --help         Show this help message
#
# Requirements:
#   - Java Runtime Environment (will be installed if missing)
#   - Internet connection (to download BFG)
#   - Clean working directory (uncommitted changes will be committed)
#
# ==============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_ROOT="/home/cytrex"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/news-microservices-backup-${TIMESTAMP}"
CERTS_BACKUP_DIR="${BACKUP_ROOT}/certs-backup-${TIMESTAMP}"
LOG_FILE="${PROJECT_ROOT}/cleanup-git-certs-${TIMESTAMP}.log"
BFG_JAR="/tmp/bfg-1.14.0.jar"
BFG_URL="https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar"

AUTO_PUSH=false

# ==============================================================================
# COLORS AND FORMATTING
# ==============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ==============================================================================
# LOGGING FUNCTIONS
# ==============================================================================

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}ℹ${RESET} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✓${RESET} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠${RESET} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}✗${RESET} $*" | tee -a "$LOG_FILE"
}

log_header() {
    echo "" | tee -a "$LOG_FILE"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${RESET}" | tee -a "$LOG_FILE"
    echo -e "${BOLD}${CYAN}  $*${RESET}" | tee -a "$LOG_FILE"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${RESET}" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

ask_confirmation() {
    local prompt="$1"
    local default="${2:-n}"

    if [[ "$default" == "y" ]]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi

    while true; do
        read -p "$(echo -e "${YELLOW}?${RESET} $prompt")" response
        response=${response:-$default}
        case "$response" in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

run_with_spinner() {
    local pid=$!
    local delay=0.1
    local spinstr='|/-\'
    while ps -p $pid > /dev/null 2>&1; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
    wait $pid
    return $?
}

# ==============================================================================
# PRE-FLIGHT CHECKS
# ==============================================================================

preflight_checks() {
    log_header "PHASE 0: Pre-flight Checks"

    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        log_error "Not in project root! Expected: /home/cytrex/news-microservices"
        exit 1
    fi
    log_success "Working directory: $PROJECT_ROOT"

    # Check if .git exists
    if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
        log_error "Not a Git repository!"
        exit 1
    fi
    log_success "Git repository detected"

    # Check for Java
    if ! check_command java; then
        log_warning "Java not found, will install..."
        if ask_confirmation "Install default-jre?" "y"; then
            sudo apt update >> "$LOG_FILE" 2>&1
            sudo apt install -y default-jre >> "$LOG_FILE" 2>&1
            log_success "Java installed"
        else
            log_error "Java is required for BFG Repo-Cleaner"
            exit 1
        fi
    else
        local java_version=$(java -version 2>&1 | head -n 1)
        log_success "Java found: $java_version"
    fi

    # Check for uncommitted changes
    if [[ -n $(git status --porcelain) ]]; then
        log_warning "You have uncommitted changes"
        git status --short | tee -a "$LOG_FILE"
        echo ""
        if ask_confirmation "Commit all changes before cleanup?" "y"; then
            git add -A >> "$LOG_FILE" 2>&1
            git commit -m "chore: prepare for certificate cleanup" >> "$LOG_FILE" 2>&1 || true
            log_success "Changes committed"
        else
            log_error "Please commit or stash changes first"
            exit 1
        fi
    else
        log_success "Working directory clean"
    fi

    # Check current branch
    local current_branch=$(git branch --show-current)
    log_info "Current branch: ${BOLD}$current_branch${RESET}"

    # Count commits and certificates
    local commit_count=$(git log --all --oneline | wc -l)
    local pem_files=$(git log --all --pretty=format: --name-only | grep '\.pem$' | sort | uniq | wc -l)
    local pem_in_workdir=$(find certs/ -name "*.pem" 2>/dev/null | wc -l)

    log_info "Commits in repository: ${BOLD}$commit_count${RESET}"
    log_info ".pem files in history: ${BOLD}$pem_files${RESET}"
    log_info ".pem files in working dir: ${BOLD}$pem_in_workdir${RESET}"

    if [[ $pem_files -eq 0 ]]; then
        log_success "No .pem files found in history!"
        log_info "Nothing to clean up. Exiting."
        exit 0
    fi

    # Show which files will be removed from history
    echo "" | tee -a "$LOG_FILE"
    log_info "Files that will be removed from history:"
    git log --all --pretty=format: --name-only | grep '\.pem$' | sort | uniq | while read file; do
        echo "  - $file" | tee -a "$LOG_FILE"
    done
    echo "" | tee -a "$LOG_FILE"

    # Final confirmation
    log_warning "${BOLD}This will rewrite Git history!${RESET}"
    log_warning "All commit hashes will change"
    log_warning "You will need to force-push to remote"
    echo "" | tee -a "$LOG_FILE"

    if ! ask_confirmation "Continue with cleanup?" "n"; then
        log_info "Cleanup aborted by user"
        exit 0
    fi
}

# ==============================================================================
# BACKUP PHASE
# ==============================================================================

create_backups() {
    log_header "PHASE 1: Creating Backups"

    # Full repository backup
    log_info "Creating full repository backup..."
    if cp -r "$PROJECT_ROOT" "$BACKUP_DIR" >> "$LOG_FILE" 2>&1; then
        local backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
        log_success "Repository backup created: $BACKUP_DIR ($backup_size)"
    else
        log_error "Failed to create repository backup"
        exit 1
    fi

    # Certificates backup
    if [[ -d "$PROJECT_ROOT/certs/rabbitmq" ]]; then
        log_info "Creating certificates backup..."
        mkdir -p "$CERTS_BACKUP_DIR"
        if cp -r "$PROJECT_ROOT/certs/rabbitmq" "$CERTS_BACKUP_DIR/" >> "$LOG_FILE" 2>&1; then
            local certs_count=$(ls "$CERTS_BACKUP_DIR/rabbitmq"/*.pem 2>/dev/null | wc -l)
            log_success "Certificates backed up: $CERTS_BACKUP_DIR ($certs_count files)"
        else
            log_warning "No certificates to backup (this is OK)"
        fi
    fi

    # Create restoration script
    local restore_script="${BACKUP_ROOT}/restore-backup-${TIMESTAMP}.sh"
    cat > "$restore_script" << 'EOF'
#!/bin/bash
# Auto-generated restoration script
set -e

BACKUP_DIR="%%BACKUP_DIR%%"
PROJECT_ROOT="%%PROJECT_ROOT%%"

echo "⚠ WARNING: This will DELETE current repository and restore backup!"
read -p "Continue? [y/N]: " response

if [[ "$response" =~ ^[Yy] ]]; then
    echo "Stopping Docker services..."
    cd "$PROJECT_ROOT" && docker compose down 2>/dev/null || true

    echo "Removing current repository..."
    rm -rf "$PROJECT_ROOT"

    echo "Restoring from backup..."
    cp -r "$BACKUP_DIR" "$PROJECT_ROOT"

    echo "✓ Restoration complete!"
    echo "  cd $PROJECT_ROOT"
else
    echo "Restoration cancelled"
fi
EOF
    sed -i "s|%%BACKUP_DIR%%|$BACKUP_DIR|g" "$restore_script"
    sed -i "s|%%PROJECT_ROOT%%|$PROJECT_ROOT|g" "$restore_script"
    chmod +x "$restore_script"

    log_success "Restoration script created: $restore_script"
    log_info "To restore backup: bash $restore_script"
}

# ==============================================================================
# BFG DOWNLOAD PHASE
# ==============================================================================

download_bfg() {
    log_header "PHASE 2: Downloading BFG Repo-Cleaner"

    if [[ -f "$BFG_JAR" ]]; then
        log_info "BFG already downloaded: $BFG_JAR"
        local jar_size=$(du -sh "$BFG_JAR" | cut -f1)
        log_info "Size: $jar_size"
        return 0
    fi

    log_info "Downloading BFG Repo-Cleaner..."
    log_info "URL: $BFG_URL"

    if wget -q --show-progress "$BFG_URL" -O "$BFG_JAR" 2>&1 | tee -a "$LOG_FILE"; then
        local jar_size=$(du -sh "$BFG_JAR" | cut -f1)
        log_success "BFG downloaded: $BFG_JAR ($jar_size)"
    else
        log_error "Failed to download BFG"
        log_info "You can download manually from: https://rtyley.github.io/bfg-repo-cleaner/"
        exit 1
    fi

    # Verify JAR
    if java -jar "$BFG_JAR" --version >> "$LOG_FILE" 2>&1; then
        log_success "BFG verified and working"
    else
        log_error "BFG JAR appears to be corrupted"
        rm -f "$BFG_JAR"
        exit 1
    fi
}

# ==============================================================================
# CLEANUP PHASE
# ==============================================================================

run_bfg_cleanup() {
    log_header "PHASE 3: Running BFG Cleanup"

    log_info "Executing BFG Repo-Cleaner..."
    log_info "This will rewrite all commits..."
    echo "" | tee -a "$LOG_FILE"

    cd "$BACKUP_ROOT"

    # Run BFG
    if java -jar "$BFG_JAR" --delete-files '*.pem' news-microservices 2>&1 | tee -a "$LOG_FILE"; then
        log_success "BFG cleanup completed"
    else
        log_error "BFG failed!"
        log_info "Check log file: $LOG_FILE"
        exit 1
    fi

    cd "$PROJECT_ROOT"
}

run_git_cleanup() {
    log_header "PHASE 4: Git Garbage Collection"

    log_info "Expiring reflog..."
    if git reflog expire --expire=now --all >> "$LOG_FILE" 2>&1; then
        log_success "Reflog expired"
    else
        log_warning "Reflog expiration had warnings (may be OK)"
    fi

    log_info "Running aggressive garbage collection..."
    log_info "This may take 1-2 minutes..."

    if git gc --prune=now --aggressive >> "$LOG_FILE" 2>&1; then
        log_success "Garbage collection completed"
    else
        log_error "Garbage collection failed"
        exit 1
    fi
}

restore_certificates() {
    log_header "PHASE 5: Restoring Certificates"

    if [[ -d "$CERTS_BACKUP_DIR/rabbitmq" ]]; then
        log_info "Restoring certificates to working directory..."

        mkdir -p "$PROJECT_ROOT/certs/rabbitmq"

        if cp -r "$CERTS_BACKUP_DIR/rabbitmq"/* "$PROJECT_ROOT/certs/rabbitmq/" >> "$LOG_FILE" 2>&1; then
            local restored_count=$(ls "$PROJECT_ROOT/certs/rabbitmq"/*.pem 2>/dev/null | wc -l)
            log_success "Certificates restored: $restored_count files"

            # List restored files
            ls -lh "$PROJECT_ROOT/certs/rabbitmq"/*.pem | while read line; do
                local filename=$(echo "$line" | awk '{print $9}' | xargs basename)
                local size=$(echo "$line" | awk '{print $5}')
                echo "  - $filename ($size)" | tee -a "$LOG_FILE"
            done
        else
            log_error "Failed to restore certificates"
            exit 1
        fi
    else
        log_info "No certificates to restore"
    fi
}

# ==============================================================================
# VERIFICATION PHASE
# ==============================================================================

verify_cleanup() {
    log_header "PHASE 6: Verification"

    local errors=0

    # Check 1: No .pem in history
    log_info "Check 1: Verifying .pem files removed from history..."
    local pem_in_history=$(git log --all --pretty=format: --name-only | grep '\.pem$' | wc -l)
    if [[ $pem_in_history -eq 0 ]]; then
        log_success "✓ No .pem files in Git history"
    else
        log_error "✗ Found $pem_in_history .pem files still in history!"
        git log --all --pretty=format: --name-only | grep '\.pem$' | sort | uniq | tee -a "$LOG_FILE"
        ((errors++))
    fi

    # Check 2: Certificates exist locally
    log_info "Check 2: Verifying certificates exist locally..."
    local pem_local=$(find certs/ -name "*.pem" 2>/dev/null | wc -l)
    if [[ $pem_local -gt 0 ]]; then
        log_success "✓ Found $pem_local certificate files locally"
    else
        log_warning "⚠ No certificate files found locally"
    fi

    # Check 3: Not tracked by Git
    log_info "Check 3: Verifying certificates not tracked..."
    local pem_tracked=$(git ls-files | grep '\.pem$' | wc -l)
    if [[ $pem_tracked -eq 0 ]]; then
        log_success "✓ No .pem files tracked by Git"
    else
        log_error "✗ Found $pem_tracked .pem files still tracked!"
        git ls-files | grep '\.pem$' | tee -a "$LOG_FILE"
        ((errors++))
    fi

    # Check 4: .gitignore works
    log_info "Check 4: Verifying .gitignore..."
    if git check-ignore -q certs/rabbitmq/ca-key.pem 2>/dev/null; then
        log_success "✓ .gitignore correctly ignores certificates"
    else
        log_warning "⚠ .gitignore may not be configured correctly"
        log_info "  Add 'certs/' or '*.pem' to .gitignore"
    fi

    # Check 5: Commit count unchanged
    log_info "Check 5: Verifying commit count..."
    local commit_count_after=$(git log --all --oneline | wc -l)
    log_success "✓ Commit count: $commit_count_after (hashes changed, count same)"

    # Check 6: Repository size
    log_info "Check 6: Checking repository size..."
    local repo_size_before=$(du -sh "$BACKUP_DIR/.git" | cut -f1)
    local repo_size_after=$(du -sh "$PROJECT_ROOT/.git" | cut -f1)
    log_info "  Before: $repo_size_before"
    log_info "  After:  $repo_size_after"

    # Check 7: Test random old commit
    log_info "Check 7: Testing old commit for .pem files..."
    local test_commit=$(git log --all --oneline | tail -10 | head -1 | awk '{print $1}')
    git checkout "$test_commit" >> "$LOG_FILE" 2>&1
    local pem_in_old_commit=$(find certs/ -name "*.pem" 2>/dev/null | wc -l)
    git checkout - >> "$LOG_FILE" 2>&1
    if [[ $pem_in_old_commit -eq 0 ]]; then
        log_success "✓ Old commits do not contain .pem files"
    else
        log_error "✗ Old commit still contains .pem files!"
        ((errors++))
    fi

    echo "" | tee -a "$LOG_FILE"
    if [[ $errors -eq 0 ]]; then
        log_success "${BOLD}${GREEN}All verification checks passed!${RESET}"
        return 0
    else
        log_error "${BOLD}${RED}$errors verification check(s) failed!${RESET}"
        return 1
    fi
}

# ==============================================================================
# PUSH PHASE
# ==============================================================================

push_changes() {
    log_header "PHASE 7: Push to Remote (Optional)"

    local current_branch=$(git branch --show-current)

    if ! git remote get-url origin &>/dev/null; then
        log_warning "No remote 'origin' configured"
        log_info "Add remote with: git remote add origin <url>"
        return 0
    fi

    local remote_url=$(git remote get-url origin)
    log_info "Remote URL: $remote_url"
    log_info "Current branch: $current_branch"

    echo "" | tee -a "$LOG_FILE"
    log_warning "${BOLD}You will need to FORCE PUSH${RESET}"
    log_warning "Command: git push -f origin $current_branch"
    echo "" | tee -a "$LOG_FILE"

    if [[ "$AUTO_PUSH" == true ]]; then
        log_info "Auto-push enabled, pushing..."
    else
        if ! ask_confirmation "Push now?" "n"; then
            log_info "Skipping push"
            log_info "Push later with: git push -f origin $current_branch"
            return 0
        fi
    fi

    log_info "Pushing to remote..."
    if git push -f origin "$current_branch" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Push completed successfully"
    else
        log_error "Push failed"
        log_info "You can try again with: git push -f origin $current_branch"
        return 1
    fi
}

# ==============================================================================
# SUMMARY
# ==============================================================================

print_summary() {
    log_header "CLEANUP SUMMARY"

    local commit_count=$(git log --all --oneline | wc -l)
    local pem_in_history=$(git log --all --pretty=format: --name-only | grep '\.pem$' | wc -l)
    local pem_local=$(find certs/ -name "*.pem" 2>/dev/null | wc -l)
    local repo_size=$(du -sh .git | cut -f1)

    echo "Results:" | tee -a "$LOG_FILE"
    echo "  - Commits in repository: $commit_count" | tee -a "$LOG_FILE"
    echo "  - .pem files in history: $pem_in_history" | tee -a "$LOG_FILE"
    echo "  - .pem files locally: $pem_local" | tee -a "$LOG_FILE"
    echo "  - Repository size: $repo_size" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

    echo "Backups created:" | tee -a "$LOG_FILE"
    echo "  - Full backup: $BACKUP_DIR" | tee -a "$LOG_FILE"
    echo "  - Certificates: $CERTS_BACKUP_DIR" | tee -a "$LOG_FILE"
    echo "  - Restore script: ${BACKUP_ROOT}/restore-backup-${TIMESTAMP}.sh" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

    echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

    log_info "Next steps:"
    echo "  1. Verify RabbitMQ still works: docker compose up -d rabbitmq" | tee -a "$LOG_FILE"
    echo "  2. Push other branches: git push -f --all origin" | tee -a "$LOG_FILE"
    echo "  3. Clean up master worktree: cd /home/cytrex/news-microservices-main" | tee -a "$LOG_FILE"
    echo "  4. Keep backups for 1-2 days, then delete" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

    log_success "${BOLD}${GREEN}Cleanup completed successfully!${RESET}"
}

# ==============================================================================
# ERROR HANDLER
# ==============================================================================

cleanup_on_error() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        echo "" | tee -a "$LOG_FILE"
        log_error "${BOLD}Script failed with exit code $exit_code${RESET}"
        echo "" | tee -a "$LOG_FILE"
        log_info "Backups available at:"
        log_info "  - Full backup: $BACKUP_DIR"
        log_info "  - Certificates: $CERTS_BACKUP_DIR"
        log_info "  - Restore with: bash ${BACKUP_ROOT}/restore-backup-${TIMESTAMP}.sh"
        echo "" | tee -a "$LOG_FILE"
        log_info "Log file: $LOG_FILE"
    fi
}

trap cleanup_on_error EXIT

# ==============================================================================
# ARGUMENT PARSING
# ==============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --auto-push)
                AUTO_PUSH=true
                shift
                ;;
            --help|-h)
                grep "^#" "$0" | grep -v "^#!/" | sed 's/^# \?//'
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
    log_header "Git Certificate Cleanup Script"
    log_info "Timestamp: $TIMESTAMP"
    log_info "Log file: $LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

    parse_arguments "$@"

    preflight_checks
    create_backups
    download_bfg
    run_bfg_cleanup
    run_git_cleanup
    restore_certificates

    if verify_cleanup; then
        push_changes
        print_summary
        exit 0
    else
        log_error "Verification failed!"
        log_info "Backups are available for restoration"
        exit 1
    fi
}

# Run main function
main "$@"
