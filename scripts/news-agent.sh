#!/bin/bash
##############################################################################
# News Agent CLI - Terminal Interface for Agent Service
#
# Usage:
#   ./news-agent.sh                        # Interactive mode
#   ./news-agent.sh "Your query here"      # Direct query mode
#   ./news-agent.sh --history              # Show conversation history
#   ./news-agent.sh --conversation ID      # Show specific conversation
#
# Requirements:
#   - curl
#   - jq
#   - Agent Service running on port 8110
#   - Auth Service running on port 8100
##############################################################################

# Configuration
AGENT_URL="${AGENT_URL:-http://localhost:8110}"
AUTH_URL="${AUTH_URL:-http://localhost:8100}"
EMAIL="${NEWS_AGENT_EMAIL:-andreas@test.com}"
PASSWORD="${NEWS_AGENT_PASSWORD:-Aug2012#}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Token cache file
TOKEN_CACHE="/tmp/.news-agent-token"
TOKEN_EXPIRY="/tmp/.news-agent-token-expiry"

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  🤖 News Agent CLI${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_dependencies() {
    local missing=()

    command -v curl >/dev/null 2>&1 || missing+=("curl")
    command -v jq >/dev/null 2>&1 || missing+=("jq")

    if [ ${#missing[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing[*]}"
        echo "Install with: sudo apt-get install ${missing[*]}"
        exit 1
    fi
}

check_services() {
    print_info "Checking service availability..."

    # Check Auth Service
    if ! curl -s -f "$AUTH_URL/health" > /dev/null 2>&1; then
        print_error "Auth Service not reachable at $AUTH_URL"
        print_info "Make sure the service is running: docker ps | grep auth-service"
        exit 1
    fi

    # Check Agent Service
    if ! curl -s -f "$AGENT_URL/health" > /dev/null 2>&1; then
        print_error "Agent Service not reachable at $AGENT_URL"
        print_info "Make sure the service is running: docker ps | grep agent-service"
        exit 1
    fi

    print_success "All services are reachable"
}

##############################################################################
# Authentication
##############################################################################

is_token_valid() {
    if [ ! -f "$TOKEN_CACHE" ] || [ ! -f "$TOKEN_EXPIRY" ]; then
        return 1
    fi

    local expiry=$(cat "$TOKEN_EXPIRY")
    local now=$(date +%s)

    if [ "$now" -ge "$expiry" ]; then
        return 1
    fi

    return 0
}

get_token() {
    # Check if cached token is still valid
    if is_token_valid; then
        cat "$TOKEN_CACHE"
        return 0
    fi

    print_info "Authenticating..."

    local response=$(curl -s -X POST "$AUTH_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" 2>/dev/null)

    if [ $? -ne 0 ]; then
        print_error "Authentication request failed"
        return 1
    fi

    local token=$(echo "$response" | jq -r '.access_token' 2>/dev/null)

    if [ -z "$token" ] || [ "$token" = "null" ]; then
        print_error "Authentication failed - invalid credentials"
        echo "Response: $response" >&2
        return 1
    fi

    # Cache token (expires in 25 minutes)
    echo "$token" > "$TOKEN_CACHE"
    local expiry=$(($(date +%s) + 1500))
    echo "$expiry" > "$TOKEN_EXPIRY"

    print_success "Authenticated successfully"
    echo "$token"
    return 0
}

##############################################################################
# Agent Operations
##############################################################################

invoke_agent() {
    local query="$1"
    local token="$2"

    if [ -z "$query" ]; then
        print_error "Query cannot be empty"
        return 1
    fi

    echo ""
    print_info "Processing query: ${YELLOW}$query${NC}"
    echo ""

    # Show loading indicator
    local pid
    (
        while true; do
            for s in / - \\ \|; do
                printf "\r${CYAN}⏳ Agent is working... $s${NC}"
                sleep 0.1
            done
        done
    ) &
    pid=$!

    # Invoke agent
    local response=$(curl -s -X POST "$AGENT_URL/api/v1/agent/invoke" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "{\"query\":\"$query\"}" \
        --max-time 180 2>/dev/null)

    # Stop loading indicator
    kill $pid 2>/dev/null
    wait $pid 2>/dev/null
    printf "\r\033[K"  # Clear loading line

    if [ $? -ne 0 ]; then
        print_error "Request failed or timed out"
        return 1
    fi

    # Parse response
    local status=$(echo "$response" | jq -r '.status' 2>/dev/null)

    if [ "$status" = "null" ] || [ -z "$status" ]; then
        print_error "Invalid response from agent"
        echo "Response: $response" >&2
        return 1
    fi

    # Display results
    display_result "$response"
}

display_result() {
    local response="$1"

    local conversation_id=$(echo "$response" | jq -r '.conversation_id')
    local status=$(echo "$response" | jq -r '.status')
    local result=$(echo "$response" | jq -r '.result')
    local exec_time=$(echo "$response" | jq -r '.execution_time_seconds')
    local tokens=$(echo "$response" | jq -r '.tokens_used.total_tokens')
    local tool_count=$(echo "$response" | jq -r '.tool_calls | length')

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  RESULT${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    if [ "$status" = "COMPLETED" ]; then
        echo -e "${GREEN}Status:${NC} ✅ $status"
    else
        echo -e "${RED}Status:${NC} ❌ $status"
    fi

    echo -e "${CYAN}Result:${NC} $result"
    echo ""
    echo -e "${YELLOW}Conversation ID:${NC} $conversation_id"
    echo -e "${YELLOW}Tool Calls:${NC} $tool_count"
    echo -e "${YELLOW}Execution Time:${NC} ${exec_time}s"
    echo -e "${YELLOW}Tokens Used:${NC} $tokens"

    # Display tool calls
    if [ "$tool_count" -gt 0 ]; then
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}  TOOL CALLS${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        local i=0
        while [ $i -lt $tool_count ]; do
            local tool_name=$(echo "$response" | jq -r ".tool_calls[$i].tool_name")
            local tool_status=$(echo "$response" | jq -r ".tool_calls[$i].status")
            local tool_duration=$(echo "$response" | jq -r ".tool_calls[$i].duration_seconds")

            if [ "$tool_status" = "SUCCESS" ]; then
                echo -e "${GREEN}✓${NC} ${BLUE}$tool_name${NC} (${tool_duration}s)"
            else
                echo -e "${RED}✗${NC} ${BLUE}$tool_name${NC} (${tool_duration}s)"
            fi

            i=$((i + 1))
        done
    fi

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

##############################################################################
# History Operations
##############################################################################

show_history() {
    local token="$1"
    local limit="${2:-10}"

    print_info "Fetching conversation history..."

    local response=$(curl -s -X GET "$AGENT_URL/api/v1/agent/conversations?limit=$limit" \
        -H "Authorization: Bearer $token" 2>/dev/null)

    if [ $? -ne 0 ]; then
        print_error "Failed to fetch history"
        return 1
    fi

    local total=$(echo "$response" | jq -r '.total')

    if [ "$total" = "0" ]; then
        print_info "No conversations found"
        return 0
    fi

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  CONVERSATION HISTORY (${total} total)${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local i=0
    while [ $i -lt $(echo "$response" | jq -r '.conversations | length') ]; do
        local conv=$(echo "$response" | jq -r ".conversations[$i]")
        local id=$(echo "$conv" | jq -r '.id')
        local query=$(echo "$conv" | jq -r '.query' | cut -c1-60)
        local status=$(echo "$conv" | jq -r '.status')
        local created=$(echo "$conv" | jq -r '.created_at')
        local tokens=$(echo "$conv" | jq -r '.tokens_used_total')

        if [ "$status" = "COMPLETED" ]; then
            echo -e "${GREEN}✓${NC} ${YELLOW}$id${NC}"
        else
            echo -e "${RED}✗${NC} ${YELLOW}$id${NC}"
        fi
        echo -e "   Query: ${query}..."
        echo -e "   Created: $created | Tokens: $tokens"
        echo ""

        i=$((i + 1))
    done

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

show_conversation() {
    local token="$1"
    local conv_id="$2"

    print_info "Fetching conversation details..."

    local response=$(curl -s -X GET "$AGENT_URL/api/v1/agent/conversations/$conv_id" \
        -H "Authorization: Bearer $token" 2>/dev/null)

    if [ $? -ne 0 ]; then
        print_error "Failed to fetch conversation"
        return 1
    fi

    display_result "$response"
}

##############################################################################
# Interactive Mode
##############################################################################

interactive_mode() {
    local token="$1"

    print_header
    print_success "Interactive mode - Type your queries or 'help' for commands"
    echo ""

    while true; do
        echo -n -e "${CYAN}Agent >${NC} "
        read -r input

        case "$input" in
            "")
                continue
                ;;
            "exit"|"quit"|"q")
                print_info "Goodbye!"
                exit 0
                ;;
            "help"|"h")
                show_help
                ;;
            "history")
                show_history "$token"
                ;;
            "clear")
                clear
                print_header
                ;;
            *)
                invoke_agent "$input" "$token"
                ;;
        esac

        echo ""
    done
}

show_help() {
    echo ""
    echo -e "${CYAN}Available Commands:${NC}"
    echo ""
    echo -e "  ${YELLOW}Your query here${NC}    - Execute agent workflow"
    echo -e "  ${YELLOW}history${NC}            - Show conversation history"
    echo -e "  ${YELLOW}clear${NC}              - Clear screen"
    echo -e "  ${YELLOW}help${NC}               - Show this help"
    echo -e "  ${YELLOW}exit${NC}               - Exit interactive mode"
    echo ""
}

##############################################################################
# Main
##############################################################################

main() {
    check_dependencies
    check_services

    # Get authentication token
    TOKEN=$(get_token)
    if [ $? -ne 0 ]; then
        exit 1
    fi

    # Parse command line arguments
    case "${1:-}" in
        "--history"|"-h")
            show_history "$TOKEN" "${2:-10}"
            ;;
        "--conversation"|"-c")
            if [ -z "$2" ]; then
                print_error "Conversation ID required"
                echo "Usage: $0 --conversation <id>"
                exit 1
            fi
            show_conversation "$TOKEN" "$2"
            ;;
        "--help")
            print_header
            echo "Usage:"
            echo "  $0                          # Interactive mode"
            echo "  $0 \"Your query\"             # Direct query"
            echo "  $0 --history [limit]        # Show history"
            echo "  $0 --conversation <id>      # Show conversation details"
            echo ""
            exit 0
            ;;
        "")
            # Interactive mode
            interactive_mode "$TOKEN"
            ;;
        *)
            # Direct query mode
            invoke_agent "$*" "$TOKEN"
            ;;
    esac
}

# Run main function
main "$@"
