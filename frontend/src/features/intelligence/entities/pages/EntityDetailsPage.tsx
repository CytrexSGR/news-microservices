/**
 * EntityDetailsPage - Entity detail with aliases
 *
 * Detailed view of a single canonical entity with all its aliases.
 */
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ExternalLink,
  Copy,
  Check,
  User,
  Building2,
  MapPin,
  Calendar,
  Package,
  HelpCircle,
  Tag,
  Link2,
  BarChart3,
} from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/Skeleton';
import { EntityAliasesTable } from '../components/EntityAliasesTable';
import { useEntityAliases } from '../api/useEntityAliases';
import { useCanonStats } from '../api/useCanonStats';
import type { EntityType } from '../types/entities.types';
import { getEntityTypeConfig } from '../types/entities.types';

const EntityTypeIcon = ({ type, className }: { type: EntityType; className?: string }) => {
  const iconClass = className || 'h-6 w-6';
  switch (type) {
    case 'PERSON':
      return <User className={`${iconClass} text-blue-500`} />;
    case 'ORGANIZATION':
      return <Building2 className={`${iconClass} text-purple-500`} />;
    case 'LOCATION':
      return <MapPin className={`${iconClass} text-green-500`} />;
    case 'EVENT':
      return <Calendar className={`${iconClass} text-orange-500`} />;
    case 'PRODUCT':
      return <Package className={`${iconClass} text-pink-500`} />;
    default:
      return <HelpCircle className={`${iconClass} text-gray-500`} />;
  }
};

export function EntityDetailsPage() {
  const { canonicalName } = useParams<{ canonicalName: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);

  const entityType = (searchParams.get('type') as EntityType) || 'PERSON';
  const canonicalId = searchParams.get('id');
  const decodedName = canonicalName ? decodeURIComponent(canonicalName) : '';

  const { data: aliases, isLoading: aliasesLoading } = useEntityAliases(
    decodedName || null,
    entityType
  );

  const { data: stats } = useCanonStats();

  const typeConfig = getEntityTypeConfig(entityType);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(decodedName);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Find this entity in the top entities list
  const entityStats = stats?.top_entities_by_aliases.find(
    (e) => e.canonical_name === decodedName && e.entity_type === entityType
  );

  if (!decodedName) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-12">
          <HelpCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-xl font-medium">Entity Not Found</h2>
          <p className="text-muted-foreground mt-2">
            The requested entity could not be found.
          </p>
          <Button variant="outline" onClick={() => navigate(-1)} className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <EntityTypeIcon type={entityType} className="h-8 w-8" />
              <h1 className="text-3xl font-bold">{decodedName}</h1>
              <Button
                variant="ghost"
                size="icon"
                onClick={copyToClipboard}
                className="h-8 w-8"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline" className={typeConfig.color}>
                {entityType}
              </Badge>
              {canonicalId && (
                <a
                  href={`https://www.wikidata.org/wiki/${canonicalId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-500 hover:underline"
                >
                  <Link2 className="h-4 w-4" />
                  {canonicalId}
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Aliases</CardTitle>
            <Tag className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {aliasesLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold">{aliases?.length || 0}</div>
            )}
            <p className="text-xs text-muted-foreground mt-1">Known variants</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Wikidata Status</CardTitle>
            <Link2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {canonicalId || entityStats?.wikidata_linked ? (
                <span className="text-green-600">Linked</span>
              ) : (
                <span className="text-yellow-600">Not Linked</span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {canonicalId || 'No Q-ID available'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Entity Type</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <EntityTypeIcon type={entityType} className="h-6 w-6" />
              <span className="text-2xl font-bold">{typeConfig.label}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Classification</p>
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* Aliases Section */}
      <EntityAliasesTable
        canonicalName={decodedName}
        entityType={entityType}
        canonicalId={canonicalId}
      />

      {/* Related Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
          <CardDescription>Additional operations for this entity</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {canonicalId && (
            <Button variant="outline" asChild>
              <a
                href={`https://www.wikidata.org/wiki/${canonicalId}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View on Wikidata
              </a>
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() =>
              navigate(
                `/intelligence/entities?search=${encodeURIComponent(decodedName)}`
              )
            }
          >
            Find Similar Entities
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate('/intelligence/entities/batch')}
          >
            Batch Canonicalization
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
