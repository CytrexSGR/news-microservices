import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { Users, TrendingUp, Link2, Filter } from 'lucide-react'
import type { TopEntity } from '@/types/knowledgeGraph'

interface TopEntitiesCardProps {
  entities: TopEntity[] | null
  isLoading: boolean
  availableEntityTypes?: string[]
  selectedEntityType?: string
  onEntityTypeChange?: (entityType: string | undefined) => void
}

export function TopEntitiesCard({
  entities,
  isLoading,
  availableEntityTypes = [],
  selectedEntityType,
  onEntityTypeChange
}: TopEntitiesCardProps) {
  // Common header component
  const renderHeader = () => (
    <CardHeader>
      <div className="flex items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Top Connected Entities
        </CardTitle>

        {availableEntityTypes.length > 0 && (
          <Select
            value={selectedEntityType || 'all'}
            onValueChange={(value) => onEntityTypeChange?.(value === 'all' ? undefined : value)}
          >
            <SelectTrigger className="w-[180px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {availableEntityTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>
    </CardHeader>
  )

  if (isLoading) {
    return (
      <Card>
        {renderHeader()}
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Loading top entities...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!entities || entities.length === 0) {
    return (
      <Card>
        {renderHeader()}
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            {selectedEntityType
              ? `No ${selectedEntityType} entities found`
              : 'No entities found'}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      {renderHeader()}
      <CardContent className="space-y-4">
        {entities.map((entity, index) => (
          <div
            key={`${entity.name}-${index}`}
            className="flex items-start justify-between pb-3 border-b last:border-0 last:pb-0"
          >
            <div className="flex-1 min-w-0 mr-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium text-sm truncate">{entity.name}</span>
                <Badge variant="outline" className="text-xs">
                  {entity.type}
                </Badge>
              </div>

              <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
                <Link2 className="h-3 w-3" />
                <span>{entity.connection_count} connections</span>
              </div>

              {entity.sample_connections && entity.sample_connections.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {entity.sample_connections.slice(0, 3).map((conn, connIndex) => (
                    <span
                      key={connIndex}
                      className="text-xs bg-muted px-1.5 py-0.5 rounded"
                      title={`${conn.relationship_type}: ${conn.name}`}
                    >
                      {conn.name}
                    </span>
                  ))}
                  {entity.sample_connections.length > 3 && (
                    <span className="text-xs text-muted-foreground px-1">
                      +{entity.sample_connections.length - 3} more
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="flex items-center gap-1 text-primary">
              <TrendingUp className="h-4 w-4" />
              <span className="text-sm font-semibold">#{index + 1}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
