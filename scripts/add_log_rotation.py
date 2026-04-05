#!/usr/bin/env python3
"""Add logging configuration to all services in docker-compose.yml"""

import re
import sys

def add_logging_to_services(content):
    """Add 'logging: *default-logging' to all services that don't have it"""

    # Find all service definitions
    services_section_match = re.search(r'^services:\s*$', content, re.MULTILINE)
    if not services_section_match:
        print("ERROR: Could not find 'services:' section")
        return content

    lines = content.split('\n')
    result_lines = []
    in_services = False
    current_service_indent = None
    service_count = 0
    added_count = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        result_lines.append(line)

        # Check if we're in services section
        if line.strip() == 'services:':
            in_services = True
            i += 1
            continue

        if in_services:
            # Check if this is a new service definition (2-space indent + name + colon)
            if re.match(r'^  [a-z][a-z0-9-]+:\s*$', line):
                service_count += 1
                current_service_indent = True

                # Look ahead to see if this service already has logging
                has_logging = False
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    # If we hit another service or end of services, stop
                    if re.match(r'^  [a-z][a-z0-9-]+:\s*$', next_line):
                        break
                    if next_line.strip() and not next_line.startswith('  '):
                        break
                    if re.match(r'^    logging:', next_line):
                        has_logging = True
                        break
                    j += 1

                # If no logging found, add it after the service name
                if not has_logging:
                    result_lines.append('    logging: *default-logging')
                    added_count += 1
                    print(f"✅ Added logging to: {line.strip()[:-1]}")

        i += 1

    print(f"\n📊 Summary:")
    print(f"   Total services found: {service_count}")
    print(f"   Log rotation added to: {added_count}")

    return '\n'.join(result_lines)

if __name__ == '__main__':
    input_file = '/home/cytrex/news-microservices/docker-compose.yml'
    output_file = '/home/cytrex/news-microservices/docker-compose.yml.new'

    try:
        with open(input_file, 'r') as f:
            content = f.read()

        # Check if x-logging anchor exists
        if 'x-logging:' not in content:
            print("ERROR: x-logging anchor not found in docker-compose.yml")
            print("Please add it first at the top of the file")
            sys.exit(1)

        modified_content = add_logging_to_services(content)

        with open(output_file, 'w') as f:
            f.write(modified_content)

        print(f"\n✅ Modified docker-compose.yml saved to: {output_file}")
        print(f"   Review the changes, then:")
        print(f"   mv {output_file} {input_file}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
