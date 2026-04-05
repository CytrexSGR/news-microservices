# -*- mode: Python -*-
# Tiltfile for News Microservices
# Usage: tilt up
# Dashboard: http://localhost:10350

# Load Docker Compose configurations
docker_compose([
    'docker-compose.yml',
    'docker-compose.dev.yml'
])

# Configuration
config.define_bool("hot-reload", True, "Enable hot-reload for all services")
config.define_string_list("services", [], "List of services to run (empty = all)")
cfg = config.parse()

# Service definitions with dependency groups
infrastructure_services = [
    'postgres',
    'redis',
    'rabbitmq',
    'minio'
]

core_services = [
    'auth-service',
    'feed-service',
    'content-analysis-service',
    'scraping-service'
]

support_services = [
    'scheduler-service',
    'analytics-service',
    'notification-service',
    'osint-service',
    'research-service',
    'search-service'
]

all_app_services = core_services + support_services

# Infrastructure services (always required)
for service in infrastructure_services:
    dc_resource(service, labels=['infrastructure'])

# Core application services
for service in core_services:
    # Docker Compose resource
    dc_resource(
        service,
        labels=['core'],
        resource_deps=infrastructure_services  # Depend on infrastructure
    )

    # Live update configuration for hot-reload
    service_dir = service.replace('-service', '_service').replace('-', '_')

    # Python services hot-reload
    docker_build(
        f'news-{service}',
        f'./services/{service}',
        dockerfile=f'./services/{service}/Dockerfile.dev',
        live_update=[
            # Sync Python source files
            sync(f'./services/{service}/app', '/app/app'),
            # Restart on requirements changes
            fall_back_on(['./services/{}/requirements.txt'.format(service)]),
        ],
        only=[
            './app/',
            './requirements.txt',
            './Dockerfile.dev'
        ]
    )

# Support services
for service in support_services:
    dc_resource(
        service,
        labels=['support'],
        resource_deps=infrastructure_services + core_services  # Depend on infra + core
    )

    # Live update for support services
    docker_build(
        f'news-{service}',
        f'./services/{service}',
        dockerfile=f'./services/{service}/Dockerfile.dev',
        live_update=[
            sync(f'./services/{service}/app', '/app/app'),
            fall_back_on(['./services/{}/requirements.txt'.format(service)]),
        ],
        only=[
            './app/',
            './requirements.txt',
            './Dockerfile.dev'
        ]
    )

# Service-specific port forwards (in addition to docker-compose ports)
# Note: These are declarative - actual forwarding handled by docker-compose
k8s_resource('auth-service', port_forwards='8100:8000')
k8s_resource('feed-service', port_forwards='8101:8001')
k8s_resource('content-analysis-service', port_forwards='8102:8002')
k8s_resource('research-service', port_forwards='8103:8003')
k8s_resource('osint-service', port_forwards='8104:8004')
k8s_resource('notification-service', port_forwards='8105:8005')
k8s_resource('search-service', port_forwards='8106:8006')
k8s_resource('analytics-service', port_forwards='8107:8007')
k8s_resource('scheduler-service', port_forwards='8108:8008')
k8s_resource('scraping-service', port_forwards='8109:8109')

# Infrastructure port forwards
k8s_resource('postgres', port_forwards='5433:5432')
k8s_resource('redis', port_forwards='6380:6379')
k8s_resource('rabbitmq', port_forwards=['5673:5672', '15673:15672'])
k8s_resource('minio', port_forwards=['9001:9000', '9002:9001'])

# Custom buttons for common operations
local_resource(
    'health-check',
    cmd='make health',
    labels=['utilities'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

local_resource(
    'run-migrations',
    cmd='for svc in content-analysis-service feed-service scheduler-service auth-service; do ./scripts/run-migrations.sh $svc; done',
    labels=['utilities'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    resource_deps=['postgres']
)

local_resource(
    'rabbitmq-status',
    cmd='docker exec news-rabbitmq rabbitmqctl list_queues',
    labels=['utilities'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    resource_deps=['rabbitmq']
)

local_resource(
    'test-api',
    cmd='./scripts/test-api-workflow.sh',
    labels=['utilities'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    resource_deps=all_app_services
)

# Tilt extensions
load('ext://restart_process', 'docker_build_with_restart')

# Print helpful information
print("""
╔═══════════════════════════════════════════════════════════╗
║  News Microservices - Tilt Development Environment       ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Dashboard: http://localhost:10350                        ║
║                                                           ║
║  Services:                                                ║
║    Infrastructure: postgres, redis, rabbitmq, minio       ║
║    Core: auth, feed, content-analysis, scraping          ║
║    Support: scheduler, analytics, notification, etc.     ║
║                                                           ║
║  Features:                                                ║
║    ✅ Hot-reload on code changes                          ║
║    ✅ Real-time log streaming                             ║
║    ✅ Resource dependency management                      ║
║    ✅ One-click utility buttons                           ║
║                                                           ║
║  Useful Commands:                                         ║
║    tilt up          - Start all services                  ║
║    tilt down        - Stop all services                   ║
║    tilt logs <svc>  - View service logs                   ║
║    tilt trigger     - Manually trigger rebuild            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")

# Resource ordering hints
update_settings(max_parallel_updates=3)  # Limit parallel builds
