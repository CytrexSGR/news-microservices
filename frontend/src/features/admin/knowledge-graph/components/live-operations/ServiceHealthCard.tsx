import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Activity, Database, MessageSquare, CheckCircle2, XCircle, Clock } from 'lucide-react'
import type { HealthCheck, BasicHealth } from '@/types/knowledgeGraph'

interface ServiceHealthCardProps {
  health: HealthCheck | null
  basicHealth: BasicHealth | null
  isLoading: boolean
}

export function ServiceHealthCard({ health, basicHealth, isLoading }: ServiceHealthCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Service Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Loading service health...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!health || !basicHealth) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Service Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-destructive">
            Failed to load service health
          </div>
        </CardContent>
      </Card>
    )
  }

  const isHealthy = health.status === 'ready'
  const neo4jHealthy = health.checks.neo4j === 'healthy'
  const rabbitmqHealthy = health.checks.rabbitmq_consumer === 'healthy'

  // Format uptime
  const formatUptime = (seconds?: number) => {
    if (!seconds) return 'Unknown'

    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 24) {
      const days = Math.floor(hours / 24)
      return `${days}d ${hours % 24}h`
    }

    return `${hours}h ${minutes}m`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Service Health
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Status */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Overall Status</span>
          <Badge variant={isHealthy ? 'default' : 'destructive'}>
            {isHealthy ? (
              <>
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Healthy
              </>
            ) : (
              <>
                <XCircle className="h-3 w-3 mr-1" />
                Degraded
              </>
            )}
          </Badge>
        </div>

        {/* Neo4j Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Neo4j</span>
          </div>
          <Badge variant={neo4jHealthy ? 'default' : 'destructive'}>
            {neo4jHealthy ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>

        {/* RabbitMQ Consumer Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">RabbitMQ Consumer</span>
          </div>
          <Badge variant={rabbitmqHealthy ? 'default' : 'destructive'}>
            {rabbitmqHealthy ? 'Active' : 'Inactive'}
          </Badge>
        </div>

        {/* Uptime */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Uptime</span>
          </div>
          <span className="text-sm font-medium">
            {formatUptime(basicHealth.uptime_seconds)}
          </span>
        </div>

        {/* Version */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Version</span>
          <span className="text-sm font-medium">{basicHealth.version}</span>
        </div>
      </CardContent>
    </Card>
  )
}
