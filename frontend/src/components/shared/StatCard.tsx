import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  change?: string
  icon: React.ReactNode
  isLoading?: boolean
}

export function StatCard({ title, value, change, icon, isLoading = false }: StatCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-4 rounded" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-32 mb-2" />
          <Skeleton className="h-3 w-20" />
        </CardContent>
      </Card>
    )
  }

  const isPositiveChange = change && change.startsWith('+')
  const isNegativeChange = change && change.startsWith('-')

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-foreground">{value}</div>
        {change && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
            {isPositiveChange && <TrendingUp className="h-3 w-3 text-green-500" />}
            {isNegativeChange && <TrendingDown className="h-3 w-3 text-red-500" />}
            <span
              className={
                isPositiveChange
                  ? 'text-green-500'
                  : isNegativeChange
                  ? 'text-red-500'
                  : ''
              }
            >
              {change}
            </span>
            <span>vs last period</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
