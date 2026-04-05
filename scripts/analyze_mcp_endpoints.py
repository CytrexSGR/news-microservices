#!/usr/bin/env python3
"""
MCP Endpoint Analysis Script
Analyzes all backend services and counts their REST API endpoints
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
import json

SERVICE_DIR = Path("/home/cytrex/news-microservices/services")

def find_endpoints_in_file(file_path: Path) -> List[Dict]:
    """Find all FastAPI route definitions in a Python file"""
    endpoints = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern for @app.get/post/put/delete/patch
        app_patterns = [
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)',
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)',
        ]

        for pattern in app_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                endpoints.append({
                    "method": method,
                    "path": path,
                    "file": str(file_path.relative_to(SERVICE_DIR))
                })
    except Exception as e:
        pass

    return endpoints

def analyze_service(service_path: Path) -> Dict:
    """Analyze a single service"""
    service_name = service_path.name

    result = {
        "name": service_name,
        "path": str(service_path),
        "endpoints": [],
        "port": None,
        "has_main": False,
        "has_routers": False
    }

    # Check for main.py
    main_py = service_path / "app" / "main.py"
    if main_py.exists():
        result["has_main"] = True
        result["endpoints"].extend(find_endpoints_in_file(main_py))

    # Check for routers directory
    routers_dir = service_path / "app" / "routers"
    if routers_dir.exists():
        result["has_routers"] = True
        for router_file in routers_dir.glob("*.py"):
            result["endpoints"].extend(find_endpoints_in_file(router_file))

    # Try to find port from docker-compose or .env
    try:
        env_file = service_path / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if 'PORT' in line and '=' in line:
                        port = line.split('=')[1].strip()
                        if port.isdigit():
                            result["port"] = int(port)
                            break
    except:
        pass

    return result

def main():
    """Main analysis function"""
    print("="*80)
    print("MCP ENDPOINT ANALYSIS - News Microservices")
    print("="*80)
    print()

    services = []

    # Iterate through all service directories
    for service_dir in sorted(SERVICE_DIR.iterdir()):
        if not service_dir.is_dir():
            continue

        # Skip special directories
        if service_dir.name.startswith('.') or service_dir.name in ['_archived', 'common', 'docs', 'memory']:
            continue

        # Skip if no app directory
        app_dir = service_dir / "app"
        if not app_dir.exists():
            continue

        service_data = analyze_service(service_dir)
        services.append(service_data)

    # Print summary
    total_endpoints = 0

    print(f"{'Service':<40} {'Port':<8} {'Endpoints':<12} {'Main':<6} {'Routers'}")
    print("-"*80)

    for service in services:
        endpoint_count = len(service["endpoints"])
        total_endpoints += endpoint_count

        port_str = str(service["port"]) if service["port"] else "N/A"
        main_str = "✓" if service["has_main"] else "✗"
        routers_str = "✓" if service["has_routers"] else "✗"

        print(f"{service['name']:<40} {port_str:<8} {endpoint_count:<12} {main_str:<6} {routers_str}")

    print("-"*80)
    print(f"{'TOTAL':<40} {'':<8} {total_endpoints:<12}")
    print()

    # Save detailed analysis
    output_file = "/home/cytrex/news-microservices/scripts/mcp_endpoint_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(services, f, indent=2)

    print(f"\nDetailed analysis saved to: {output_file}")
    print()

    # Group by domain
    print("="*80)
    print("DOMAIN GROUPING (Based on analysis documents)")
    print("="*80)

    domains = {
        "Intelligence/Analysis": ["content-analysis-v3", "entity-canonicalization-service", "osint-service", "intelligence-service", "nlp-extraction-service"],
        "Search/Discovery": ["search-service", "knowledge-graph-service"],
        "Core/System": ["auth-service"],
        "Integration": ["research-service", "fmp-service", "notification-service", "scraping-service"],
        "Orchestration": ["llm-orchestrator-service", "scheduler-service", "coordination", "execution-service"],
        "Content": ["feed-service", "narrative-service"],
        "Analytics": ["analytics-service", "prediction-service"],
        "Other": ["ontology-proposals-service", "oss-service"]
    }

    for domain, service_names in domains.items():
        domain_services = [s for s in services if any(sn in s['name'] for sn in service_names)]
        domain_endpoints = sum(len(s['endpoints']) for s in domain_services)

        print(f"\n{domain}:")
        print(f"  Services: {len(domain_services)}")
        print(f"  Total Endpoints: {domain_endpoints}")

        for service in domain_services:
            print(f"    - {service['name']}: {len(service['endpoints'])} endpoints")

if __name__ == "__main__":
    main()
