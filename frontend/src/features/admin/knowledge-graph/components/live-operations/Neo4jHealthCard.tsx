import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Database, CheckCircle2, XCircle, Server, Package } from 'lucide-react'
import type { Neo4jHealth } from '@/types/knowledgeGraph'

interface Neo4jHealthCardProps {
  health: Neo4jHealth | null
  isLoading: boolean
}

export function Neo4jHealthCard({ health, isLoading }: Neo4jHealthCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Neo4j Database
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Loading Neo4j health...
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
            <Database className="h-5 w-5" />
            Neo4j Database
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-destructive">
            Failed to load Neo4j health
          </div>
        </CardContent>
      </Card>
    )
  }

  const isHealthy = health.status === 'healthy' && health.connected

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Neo4j Database
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Connection Status */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Connection</span>
          <Badge variant={isHealthy ? 'default' : 'destructive'}>
            {isHealthy ? (
              <>
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Connected
              </>
            ) : (
              <>
                <XCircle className="h-3 w-3 mr-1" />
                Disconnected
              </>
            )}
          </Badge>
        </div>

        {/* Version */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Version</span>
          </div>
          <span className="text-sm font-medium">{health.version}</span>
        </div>

        {/* Edition */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Edition</span>
          <Badge variant="outline">{health.edition}</Badge>
        </div>

        {/* Host */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Host</span>
          </div>
          <span className="text-xs font-mono text-muted-foreground">{health.host}</span>
        </div>
      </CardContent>
    </Card>
  )
}
