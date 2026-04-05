#!/bin/bash
#
# Generate RabbitMQ TLS Certificates
#
# Mitigates CVE-2025-002 (Unencrypted RabbitMQ Communication)
#
# Creates:
# - CA certificate (self-signed)
# - Server certificate (signed by CA)
# - Client certificate (optional, for mutual TLS)
#
# Usage:
#   ./scripts/generate-rabbitmq-certs.sh
#
# Output:
#   certs/rabbitmq/ca-cert.pem       - CA certificate
#   certs/rabbitmq/ca-key.pem        - CA private key
#   certs/rabbitmq/server-cert.pem   - Server certificate
#   certs/rabbitmq/server-key.pem    - Server private key
#
# Security Note:
#   - CA private key is protected (chmod 600)
#   - Certificates valid for 365 days
#   - Self-signed CA (for development/internal use)
#   - For production, use commercial CA or Let's Encrypt
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CERT_DIR="./certs/rabbitmq"
DAYS_VALID=365
KEY_SIZE=4096

# Certificate details
CA_SUBJECT="/C=DE/ST=Bavaria/L=Munich/O=News-MCP/OU=Development/CN=RabbitMQ-CA"
SERVER_SUBJECT="/C=DE/ST=Bavaria/L=Munich/O=News-MCP/OU=Development/CN=rabbitmq"

# Functions
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

check_openssl() {
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL not found. Please install: sudo apt-get install openssl"
    fi
    info "OpenSSL version: $(openssl version)"
}

create_cert_dir() {
    if [ -d "$CERT_DIR" ]; then
        warn "Certificate directory exists: $CERT_DIR"
        read -p "Overwrite existing certificates? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Aborted by user"
            exit 0
        fi
        rm -rf "$CERT_DIR"
    fi

    mkdir -p "$CERT_DIR"
    info "Created certificate directory: $CERT_DIR"
}

generate_ca_certificate() {
    info "Generating CA certificate..."

    openssl req -x509 \
        -newkey rsa:$KEY_SIZE \
        -keyout "$CERT_DIR/ca-key.pem" \
        -out "$CERT_DIR/ca-cert.pem" \
        -days $DAYS_VALID \
        -nodes \
        -subj "$CA_SUBJECT" \
        2>&1 | grep -v "writing new private key"

    if [ ! -f "$CERT_DIR/ca-cert.pem" ]; then
        error "Failed to generate CA certificate"
    fi

    info "✅ CA certificate generated: $CERT_DIR/ca-cert.pem"
}

generate_server_certificate() {
    info "Generating server certificate..."

    # Generate server private key and CSR
    openssl req -newkey rsa:$KEY_SIZE \
        -keyout "$CERT_DIR/server-key.pem" \
        -out "$CERT_DIR/server-req.pem" \
        -nodes \
        -subj "$SERVER_SUBJECT" \
        2>&1 | grep -v "writing new private key"

    # Sign server certificate with CA
    openssl x509 -req \
        -in "$CERT_DIR/server-req.pem" \
        -CA "$CERT_DIR/ca-cert.pem" \
        -CAkey "$CERT_DIR/ca-key.pem" \
        -CAcreateserial \
        -out "$CERT_DIR/server-cert.pem" \
        -days $DAYS_VALID \
        -extfile <(printf "subjectAltName=DNS:rabbitmq,DNS:localhost,IP:127.0.0.1") \
        2>&1 | grep -v "Signature ok"

    # Clean up CSR
    rm -f "$CERT_DIR/server-req.pem"

    if [ ! -f "$CERT_DIR/server-cert.pem" ]; then
        error "Failed to generate server certificate"
    fi

    info "✅ Server certificate generated: $CERT_DIR/server-cert.pem"
}

set_permissions() {
    info "Setting secure file permissions..."

    # CA private key: owner read/write only
    chmod 600 "$CERT_DIR/ca-key.pem"

    # Server private key: owner read/write only
    chmod 600 "$CERT_DIR/server-key.pem"

    # Certificates: owner read/write, group read
    chmod 640 "$CERT_DIR/ca-cert.pem"
    chmod 640 "$CERT_DIR/server-cert.pem"

    # Make directory readable by group (for docker volumes)
    chmod 750 "$CERT_DIR"

    info "✅ Permissions set (private keys: 600, certs: 640)"
}

verify_certificates() {
    info "Verifying certificates..."

    # Verify CA certificate
    if ! openssl x509 -in "$CERT_DIR/ca-cert.pem" -noout -text > /dev/null 2>&1; then
        error "Invalid CA certificate"
    fi

    # Verify server certificate
    if ! openssl x509 -in "$CERT_DIR/server-cert.pem" -noout -text > /dev/null 2>&1; then
        error "Invalid server certificate"
    fi

    # Verify certificate chain
    if ! openssl verify -CAfile "$CERT_DIR/ca-cert.pem" "$CERT_DIR/server-cert.pem" > /dev/null 2>&1; then
        error "Certificate chain verification failed"
    fi

    info "✅ All certificates verified successfully"
}

print_summary() {
    echo ""
    echo "═════════════════════════════════════════════════════════════"
    info "RabbitMQ TLS Certificates Generated Successfully"
    echo "═════════════════════════════════════════════════════════════"
    echo ""
    echo "Files created:"
    echo "  📄 $CERT_DIR/ca-cert.pem       - CA certificate (public)"
    echo "  🔑 $CERT_DIR/ca-key.pem        - CA private key (protected)"
    echo "  📄 $CERT_DIR/server-cert.pem   - Server certificate (public)"
    echo "  🔑 $CERT_DIR/server-key.pem    - Server private key (protected)"
    echo ""
    echo "Certificate details:"
    echo "  Valid for: $DAYS_VALID days"
    echo "  Key size:  $KEY_SIZE bits"
    echo "  Algorithm: RSA with SHA-256"
    echo ""
    echo "Next steps:"
    echo "  1. Update rabbitmq.conf (see CVE-2025-002 fix)"
    echo "  2. Update docker-compose.yml to mount certificates"
    echo "  3. Update RABBITMQ_URL to use amqps:// instead of amqp://"
    echo "  4. Restart RabbitMQ: docker compose restart rabbitmq"
    echo "  5. Verify TLS: openssl s_client -connect localhost:5671"
    echo ""
    echo "═════════════════════════════════════════════════════════════"
}

# Main execution
main() {
    echo ""
    echo "═════════════════════════════════════════════════════════════"
    echo "  RabbitMQ TLS Certificate Generation"
    echo "  CVE-2025-002 Mitigation"
    echo "═════════════════════════════════════════════════════════════"
    echo ""

    check_openssl
    create_cert_dir
    generate_ca_certificate
    generate_server_certificate
    set_permissions
    verify_certificates
    print_summary
}

# Run main function
main
