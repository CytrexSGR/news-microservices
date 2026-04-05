#!/usr/bin/env python3
"""
Comprehensive Service Analysis for MCP
Analyzes ALL backend services and creates detailed inventory
"""

import os
import re
from pathlib import Path
from typing import Dict, List
import json

SERVICE_DIR = Path("/home/cytrex/news-microservices/services")

def count_endpoints_in_file(file_path: Path) -> int:
    """Count FastAPI endpoints in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Patterns for FastAPI routes
        patterns = [
            r'@app\.(get|post|put|delete|patch)\(',
            r'@router\.(get|post|put|delete|patch)\(',
        ]

        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, content))

        return count
    except:
        return 0

def analyze_service_structure(service_path: Path) -> Dict:
    """Analyze a service's structure and endpoints"""
    service_name = service_path.name

    result = {
        "name": service_name,
        "has_api": False,
        "has_routers": False,
        "has_workers": False,
        "has_tests": False,
        "api_files": [],
        "router_files": [],
        "total_endpoints": 0,
        "port": None,
        "description": ""
    }

    app_dir = service_path / "app"
    if not app_dir.exists():
        return result

    # Check main.py for description
    main_py = app_dir / "main.py"
    if main_py.exists():
        try:
            with open(main_py, 'r') as f:
                content = f.read()
                # Extract description from docstring or FastAPI title
                desc_match = re.search(r'description="([^"]+)"', content)
                if desc_match:
                    result["description"] = desc_match.group(1)
                elif '"""' in content:
                    doc = content.split('"""')[1].strip()
                    result["description"] = doc.split('\n')[0]
        except:
            pass

    # Check for api directory
    api_dir = app_dir / "api"
    if api_dir.exists():
        result["has_api"] = True
        for py_file in api_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                endpoints = count_endpoints_in_file(py_file)
                if endpoints > 0:
                    result["api_files"].append({
                        "file": str(py_file.relative_to(service_path)),
                        "endpoints": endpoints
                    })
                    result["total_endpoints"] += endpoints

    # Check for routers directory
    routers_dir = app_dir / "routers"
    if routers_dir.exists():
        result["has_routers"] = True
        for py_file in routers_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                endpoints = count_endpoints_in_file(py_file)
                if endpoints > 0:
                    result["router_files"].append({
                        "file": str(py_file.relative_to(service_path)),
                        "endpoints": endpoints
                    })
                    result["total_endpoints"] += endpoints

    # Check main.py endpoints
    if main_py.exists():
        main_endpoints = count_endpoints_in_file(main_py)
        if main_endpoints > 0:
            result["total_endpoints"] += main_endpoints

    # Check for workers
    workers_dir = app_dir / "workers"
    result["has_workers"] = workers_dir.exists() if app_dir.exists() else False

    # Check for tests
    tests_dir = service_path / "tests"
    result["has_tests"] = tests_dir.exists()

    # Try to extract port from docker-compose
    # This would require parsing docker-compose.yml
    # For now, we'll use known ports
    port_map = {
        "auth-service": 8100,
        "feed-service": 8101,
        "research-service": 8103,
        "osint-service": 8104,
        "notification-service": 8105,
        "search-service": 8106,
        "analytics-service": 8107,
        "scheduler-service": 8108,
        "fmp-service": 8109,
        "knowledge-graph-service": 8111,
        "entity-canonicalization-service": 8112,
        "llm-orchestrator-service": 8113,
        "content-analysis-v3": 8117,
        "prediction-service": 8116,
        "intelligence-service": None,  # TBD
        "narrative-service": None,  # TBD
        "execution-service": None,  # TBD
        "nlp-extraction-service": None,  # No REST API
        "ontology-proposals-service": None,  # TBD
        "oss-service": None,  # TBD
        "scraping-service": None  # No REST API
    }
    result["port"] = port_map.get(service_name)

    return result

def main():
    """Main analysis function"""
    print("="*100)
    print("COMPREHENSIVE SERVICE ANALYSIS - MCP Documentation Gap Filling")
    print("="*100)
    print()

    services = []

    # Analyze all services
    for service_dir in sorted(SERVICE_DIR.iterdir()):
        if not service_dir.is_dir():
            continue

        # Skip special directories
        if service_dir.name.startswith('.') or service_dir.name in ['_archived', 'common', 'docs', 'memory']:
            continue

        service_data = analyze_service_structure(service_dir)
        if service_data["total_endpoints"] > 0 or service_data["has_api"] or service_data["has_routers"]:
            services.append(service_data)

    # Print detailed summary
    print(f"{'Service':<45} {'Port':<8} {'Endpoints':<12} {'Description'}")
    print("-"*100)

    total_endpoints = 0
    documented = 0
    missing = 0

    # Known documented services
    documented_services = {
        "auth-service", "feed-service", "research-service", "osint-service",
        "notification-service", "search-service", "analytics-service",
        "scheduler-service", "fmp-service", "knowledge-graph-service",
        "entity-canonicalization-service", "llm-orchestrator-service",
        "scraping-service"
    }

    for service in services:
        total_endpoints += service["total_endpoints"]
        status = "✅" if service["name"] in documented_services else "❌"

        if service["name"] in documented_services:
            documented += 1
        else:
            missing += 1

        port_str = str(service["port"]) if service["port"] else "TBD"
        desc = service["description"][:40] + "..." if len(service["description"]) > 40 else service["description"]

        print(f"{status} {service['name']:<42} {port_str:<8} {service['total_endpoints']:<12} {desc}")

    print("-"*100)
    print(f"{'TOTAL':<45} {'':<8} {total_endpoints:<12}")
    print()
    print(f"📊 Summary:")
    print(f"   Total Services: {len(services)}")
    print(f"   Documented: {documented} ({documented/len(services)*100:.1f}%)")
    print(f"   Missing Documentation: {missing} ({missing/len(services)*100:.1f}%)")
    print(f"   Total REST Endpoints: {total_endpoints}")
    print()

    # Save detailed JSON
    output_file = "/home/cytrex/userdocs/mcp/analysis/COMPLETE_SERVICE_INVENTORY.json"
    with open(output_file, 'w') as f:
        json.dump(services, f, indent=2)

    print(f"💾 Detailed analysis saved to: {output_file}")
    print()

    # List missing services
    print("="*100)
    print("MISSING DOCUMENTATION (Need Analysis)")
    print("="*100)

    for service in services:
        if service["name"] not in documented_services:
            print(f"\n📝 {service['name']}:")
            print(f"   Port: {service['port'] if service['port'] else 'TBD'}")
            print(f"   Endpoints: {service['total_endpoints']}")
            print(f"   Description: {service['description'] or 'N/A'}")
            print(f"   Has API dir: {service['has_api']}")
            print(f"   Has Routers: {service['has_routers']}")
            print(f"   Has Workers: {service['has_workers']}")
            print(f"   Has Tests: {service['has_tests']}")

            if service["api_files"]:
                print(f"   API Files:")
                for api_file in service["api_files"]:
                    print(f"      - {api_file['file']}: {api_file['endpoints']} endpoints")

            if service["router_files"]:
                print(f"   Router Files:")
                for router_file in service["router_files"]:
                    print(f"      - {router_file['file']}: {router_file['endpoints']} endpoints")

if __name__ == "__main__":
    main()
