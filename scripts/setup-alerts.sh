#!/bin/bash
# Alert Setup Script
# Configure webhook alerts for Docker resource monitoring

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.monitoring"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔔 Alert Configuration Setup${NC}"
echo "=============================="
echo ""

# Check if .env.monitoring exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  .env.monitoring not found. Creating template...${NC}"
    cat > "$ENV_FILE" <<EOF
# Monitoring Alert Configuration
ALERT_METHOD=log
WEBHOOK_URL=
EMAIL_TO=admin@example.com
LOG_FILE=/var/log/docker-monitor/alerts.log
EOF
    echo -e "${GREEN}✓${NC} Created $ENV_FILE"
fi

echo ""
echo "Select alert method:"
echo "  1) Log only (default, no external alerts)"
echo "  2) Slack webhook"
echo "  3) Discord webhook"
echo "  4) Email (requires mail setup)"
echo "  5) All methods"
echo ""
read -p "Choice [1-5]: " choice

case $choice in
    2)
        echo ""
        echo -e "${BLUE}Slack Webhook Setup${NC}"
        echo "1. Go to https://api.slack.com/messaging/webhooks"
        echo "2. Create Incoming Webhook"
        echo "3. Copy the webhook URL"
        echo ""
        read -p "Enter Slack webhook URL: " webhook_url

        sed -i "s|^ALERT_METHOD=.*|ALERT_METHOD=webhook|" "$ENV_FILE"
        sed -i "s|^WEBHOOK_URL=.*|WEBHOOK_URL=$webhook_url|" "$ENV_FILE"

        echo ""
        echo -e "${GREEN}✓${NC} Slack webhook configured"
        echo ""
        echo "Testing webhook..."

        curl -X POST "$webhook_url" \
            -H 'Content-Type: application/json' \
            -d '{"text":"🔔 Docker Monitor Test Alert\n\nIf you see this message, alerts are working!\n\nTimestamp: '"$(date -u +"%Y-%m-%d %H:%M:%S UTC")"'"}' \
            2>/dev/null && echo -e "${GREEN}✓${NC} Test message sent!" || echo -e "${YELLOW}⚠️${NC} Test failed - check webhook URL"
        ;;

    3)
        echo ""
        echo -e "${BLUE}Discord Webhook Setup${NC}"
        echo "1. Go to Server Settings → Integrations"
        echo "2. Create Webhook"
        echo "3. Copy the webhook URL"
        echo ""
        read -p "Enter Discord webhook URL: " webhook_url

        sed -i "s|^ALERT_METHOD=.*|ALERT_METHOD=webhook|" "$ENV_FILE"
        sed -i "s|^WEBHOOK_URL=.*|WEBHOOK_URL=$webhook_url|" "$ENV_FILE"

        echo ""
        echo -e "${GREEN}✓${NC} Discord webhook configured"
        echo ""
        echo "Testing webhook..."

        curl -X POST "$webhook_url" \
            -H 'Content-Type: application/json' \
            -d '{"content":"🔔 **Docker Monitor Test Alert**\n\nIf you see this message, alerts are working!\n\nTimestamp: '"$(date -u +"%Y-%m-%d %H:%M:%S UTC")"'"}' \
            2>/dev/null && echo -e "${GREEN}✓${NC} Test message sent!" || echo -e "${YELLOW}⚠️${NC} Test failed - check webhook URL"
        ;;

    4)
        echo ""
        echo -e "${YELLOW}Email alerts require mail client installation${NC}"
        echo "Run: sudo apt install mailutils"
        echo ""
        read -p "Email address for alerts: " email_to

        sed -i "s|^ALERT_METHOD=.*|ALERT_METHOD=email|" "$ENV_FILE"
        sed -i "s|^EMAIL_TO=.*|EMAIL_TO=$email_to|" "$ENV_FILE"

        echo -e "${GREEN}✓${NC} Email configured (requires mail client setup)"
        ;;

    5)
        echo ""
        read -p "Enter webhook URL: " webhook_url
        read -p "Email address: " email_to

        sed -i "s|^ALERT_METHOD=.*|ALERT_METHOD=all|" "$ENV_FILE"
        sed -i "s|^WEBHOOK_URL=.*|WEBHOOK_URL=$webhook_url|" "$ENV_FILE"
        sed -i "s|^EMAIL_TO=.*|EMAIL_TO=$email_to|" "$ENV_FILE"

        echo -e "${GREEN}✓${NC} All alert methods configured"
        ;;

    *)
        echo -e "${GREEN}✓${NC} Using log-only mode (default)"
        ;;
esac

echo ""
echo "─────────────────────────────────────"
echo -e "${GREEN}✅ Alert configuration complete${NC}"
echo ""
echo "Configuration file: $ENV_FILE"
echo ""
echo "To load environment variables:"
echo "  source $ENV_FILE"
echo ""
echo "To test monitoring with alerts:"
echo "  source $ENV_FILE && ./scripts/monitor-resources.sh --alert-only"
echo ""
echo "Systemd service will use these settings on next run."
