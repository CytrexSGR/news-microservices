import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/Card';
import { Target, AlertTriangle, TrendingUp, Users, Shield, Heart, MapPin } from 'lucide-react';

interface SymbolicFindingCardProps {
  symbolic: any;
  category: string;
}

export function SymbolicFindingCard({ symbolic, category }: SymbolicFindingCardProps) {
  if (!symbolic) return null;

  // EventTypeSymbolic
  if (category === 'event_type' && symbolic.event_type) {
    return (
      <Card className="p-3 bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-red-600" />
            <span className="text-sm font-semibold text-red-900 dark:text-red-100">
              Event Details
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Type:</span>
              <Badge variant="destructive" className="ml-2">{symbolic.event_type.replace(/_/g, ' ')}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Target:</span>
              <Badge variant="outline" className="ml-2">{symbolic.target}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Severity:</span>
              <Badge className="ml-2">{symbolic.severity}</Badge>
            </div>
            {symbolic.casualties && (
              <div>
                <span className="text-muted-foreground">Casualties:</span>
                <span className="ml-2 font-semibold">{symbolic.casualties}</span>
              </div>
            )}
          </div>

          {symbolic.actors && Object.keys(symbolic.actors).length > 0 && (
            <div className="mt-2">
              <span className="text-xs text-muted-foreground">Actors:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {Object.entries(symbolic.actors).map(([code, role]: [string, any]) => (
                  <Badge key={code} variant="secondary" className="text-xs">
                    {code}: {String(role)}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {symbolic.location && (
            <div className="flex items-center gap-1 text-xs">
              <MapPin className="h-3 w-3" />
              <span className="text-muted-foreground">Location:</span>
              <span className="font-medium">{symbolic.location}</span>
            </div>
          )}
        </div>
      </Card>
    );
  }

  // IHLConcernSymbolic
  if (category === 'ihl_concern' && symbolic.ihl_type) {
    return (
      <Card className="p-3 bg-orange-50 dark:bg-orange-950/20 border-orange-200 dark:border-orange-900">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-orange-600" />
            <span className="text-sm font-semibold text-orange-900 dark:text-orange-100">
              IHL Concern
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Type:</span>
              <Badge variant="destructive" className="ml-2">{symbolic.ihl_type.replace(/_/g, ' ')}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Violation Level:</span>
              <Badge className="ml-2">{symbolic.violation_level}</Badge>
            </div>
            {symbolic.affected_population && (
              <div className="col-span-2">
                <span className="text-muted-foreground">Affected Population:</span>
                <span className="ml-2 font-semibold">{symbolic.affected_population.toLocaleString()}</span>
              </div>
            )}
          </div>

          {symbolic.actors && symbolic.actors.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Responsible Actors:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {symbolic.actors.map((code: string) => (
                  <Badge key={code} variant="secondary">{code}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  // RegionalImpactSymbolic
  if (category === 'regional_impact' && symbolic.affected_countries) {
    return (
      <Card className="p-3 bg-purple-50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-900">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-semibold text-purple-900 dark:text-purple-100">
              Regional Impact
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Impact Type:</span>
              <Badge variant="secondary" className="ml-2">{symbolic.impact_type}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Stability:</span>
              <Badge className="ml-2">{symbolic.regional_stability}</Badge>
            </div>
            {symbolic.severity !== undefined && (
              <div>
                <span className="text-muted-foreground">Severity:</span>
                <span className="ml-2 font-semibold">{(symbolic.severity * 100).toFixed(0)}%</span>
              </div>
            )}
            {symbolic.spillover_risk !== undefined && (
              <div>
                <span className="text-muted-foreground">Spillover Risk:</span>
                <span className="ml-2 font-semibold">{(symbolic.spillover_risk * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>

          {symbolic.affected_countries.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Affected Countries:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {symbolic.affected_countries.map((code: string) => (
                  <Badge key={code} variant="secondary">{code}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  // FinancialImpactSymbolic
  if (category === 'financial_impact' && symbolic.markets) {
    return (
      <Card className="p-3 bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-600" />
            <span className="text-sm font-semibold text-green-900 dark:text-green-100">
              Financial Impact
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            {symbolic.volatility && (
              <div>
                <span className="text-muted-foreground">Volatility:</span>
                <Badge variant="secondary" className="ml-2">{symbolic.volatility}</Badge>
              </div>
            )}
            {symbolic.duration && (
              <div>
                <span className="text-muted-foreground">Duration:</span>
                <Badge variant="outline" className="ml-2">{symbolic.duration.replace(/_/g, ' ')}</Badge>
              </div>
            )}
          </div>

          {Object.keys(symbolic.markets).length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Market Changes:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {Object.entries(symbolic.markets).map(([market, change]: [string, any]) => {
                  const changeNum = Number(change);
                  const isPositive = changeNum > 0;
                  return (
                    <Badge
                      key={market}
                      variant={isPositive ? "default" : "destructive"}
                      className="text-xs"
                    >
                      {market}: {isPositive ? '+' : ''}{(changeNum * 100).toFixed(2)}%
                    </Badge>
                  );
                })}
              </div>
            </div>
          )}

          {symbolic.sectors && Object.keys(symbolic.sectors).length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Sector Impact:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {Object.entries(symbolic.sectors).map(([sector, direction]: [string, any]) => (
                  <Badge key={sector} variant="secondary" className="text-xs">
                    {sector}: {String(direction)}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  // PoliticalDevelopmentSymbolic
  if (category === 'political_development' && symbolic.policy_area) {
    return (
      <Card className="p-3 bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-semibold text-blue-900 dark:text-blue-100">
              Political Development
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Policy Area:</span>
              <Badge variant="secondary" className="ml-2">{symbolic.policy_area}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Direction:</span>
              <Badge variant="outline" className="ml-2">{symbolic.direction?.replace(/_/g, ' ')}</Badge>
            </div>
            {symbolic.impact_level && (
              <div className="col-span-2">
                <span className="text-muted-foreground">Impact Level:</span>
                <Badge className="ml-2">{symbolic.impact_level}</Badge>
              </div>
            )}
          </div>

          {symbolic.actors && Object.keys(symbolic.actors).length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Actors:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {Object.entries(symbolic.actors).map(([code, stance]: [string, any]) => (
                  <Badge key={code} variant="secondary" className="text-xs">
                    {code}: {stance.position || 'N/A'}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {symbolic.affected_countries && symbolic.affected_countries.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Affected Countries:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {symbolic.affected_countries.map((code: string) => (
                  <Badge key={code} variant="secondary">{code}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  // SecurityThreatSymbolic
  if (category === 'security_threat' && symbolic.threat_type) {
    return (
      <Card className="p-3 bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-900">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-yellow-600" />
            <span className="text-sm font-semibold text-yellow-900 dark:text-yellow-100">
              Security Threat
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Threat Type:</span>
              <Badge variant="destructive" className="ml-2">{symbolic.threat_type}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Imminence:</span>
              <Badge className="ml-2">{symbolic.imminence}</Badge>
            </div>
            {symbolic.severity !== undefined && (
              <div>
                <span className="text-muted-foreground">Severity:</span>
                <span className="ml-2 font-semibold">{(symbolic.severity * 100).toFixed(0)}%</span>
              </div>
            )}
            {symbolic.confidence !== undefined && (
              <div>
                <span className="text-muted-foreground">Confidence:</span>
                <span className="ml-2 font-semibold">{(symbolic.confidence * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>

          {symbolic.source && symbolic.source.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Source:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {symbolic.source.map((code: string) => (
                  <Badge key={code} variant="secondary">{code}</Badge>
                ))}
              </div>
            </div>
          )}

          {symbolic.target && symbolic.target.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Target:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {symbolic.target.map((code: string) => (
                  <Badge key={code} variant="secondary">{code}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  // HumanitarianCrisisSymbolic
  if (category === 'humanitarian_crisis' && symbolic.crisis_type) {
    return (
      <Card className="p-3 bg-pink-50 dark:bg-pink-950/20 border-pink-200 dark:border-pink-900">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Heart className="h-4 w-4 text-pink-600" />
            <span className="text-sm font-semibold text-pink-900 dark:text-pink-100">
              Humanitarian Crisis
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Crisis Type:</span>
              <Badge variant="destructive" className="ml-2">{symbolic.crisis_type}</Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Severity:</span>
              <Badge className="ml-2">{symbolic.severity}</Badge>
            </div>
            {symbolic.affected_population && (
              <div className="col-span-2">
                <span className="text-muted-foreground">Affected Population:</span>
                <span className="ml-2 font-semibold">{symbolic.affected_population.toLocaleString()}</span>
              </div>
            )}
          </div>

          {symbolic.location && (
            <div className="flex items-center gap-1 text-xs">
              <MapPin className="h-3 w-3" />
              <span className="text-muted-foreground">Location:</span>
              <span className="font-medium">{symbolic.location}</span>
            </div>
          )}

          {symbolic.urgent_needs && symbolic.urgent_needs.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Urgent Needs:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {symbolic.urgent_needs.map((need: string) => (
                  <Badge key={need} variant="secondary">{need}</Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  return null;
}
