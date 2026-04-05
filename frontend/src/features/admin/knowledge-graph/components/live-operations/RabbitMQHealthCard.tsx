import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { MessageSquare, CheckCircle2, XCircle, Inbox, Users } from 'lucide-react'
import type { RabbitMQHealth } from '@/types/knowledgeGraph'

interface RabbitMQHealthCardProps {
  health: RabbitMQHealth | null
  isLoading: boolean
}

export function RabbitMQHealthCard({ health, isLoading }: RabbitMQHealthCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            RabbitMQ Consumer
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Loading RabbitMQ health...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!health) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            RabbitMQ Consumer
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-destructive">
            Failed to load RabbitMQ health
          </div>
        </CardContent>
      </Card>
    )
  }

  const isHealthy = health.status === 'healthy' && health.connection === 'open' && health.channel === 'open'
  const hasBacklog = health.queue.message_count > 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          RabbitMQ Consumer
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Connection Status */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Status</span>
          <Badge variant={isHealthy ? 'default' : 'destructive'}>
            {isHealthy ? (
              <>
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Healthy
              </>
            ) : (
              <>
                <XCircle className="h-3 w-3 mr-1" />
                Unhealthy
              </>
            )}
          </Badge>
        </div>

        {/* Queue Name */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Queue</span>
          <span className="text-xs font-mono">{health.queue.name}</span>
        </div>

        {/* Queue Size */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Inbox className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Queue Size</span>
          </div>
          <Badge variant={hasBacklog ? 'outline' : 'secondary'}>
            {health.queue.message_count} messages
          </Badge>
        </div>

        {/* Consumer Count */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Consumers</span>
          </div>
          <span className="text-sm font-medium">{health.queue.consumer_count}</span>
        </div>

        {/* Exchange */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Exchange</span>
          <span className="text-xs font-mono">{health.exchange}</span>
        </div>

        {/* Routing Key */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Routing Key</span>
          <span className="text-xs font-mono">{health.routing_key}</span>
        </div>
      </CardContent>
    </Card>
  )
}
