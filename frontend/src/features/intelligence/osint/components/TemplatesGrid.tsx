/**
 * TemplatesGrid - OSINT Templates Card Grid
 *
 * Displays available OSINT templates in a responsive grid
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Share2,
  Globe,
  Shield,
  Network,
  DollarSign,
  User,
  Building,
  FileSearch,
  Clock,
  ChevronRight,
} from 'lucide-react';
import { useOsintTemplatesByCategory } from '../api';
import type { OsintTemplate, OsintCategory } from '../types/osint.types';
import { getCategoryLabel } from '../types/osint.types';

interface TemplatesGridProps {
  onTemplateSelect?: (template: OsintTemplate) => void;
  selectedCategory?: OsintCategory;
}

const categoryIcons: Record<OsintCategory, React.ReactNode> = {
  social_media: <Share2 className="h-5 w-5" />,
  domain_analysis: <Globe className="h-5 w-5" />,
  threat_intelligence: <Shield className="h-5 w-5" />,
  network_analysis: <Network className="h-5 w-5" />,
  financial: <DollarSign className="h-5 w-5" />,
  person: <User className="h-5 w-5" />,
  organization: <Building className="h-5 w-5" />,
};

export function TemplatesGrid({ onTemplateSelect, selectedCategory }: TemplatesGridProps) {
  const { templates, groupedTemplates, isLoading, error } = useOsintTemplatesByCategory();

  if (isLoading) {
    return <TemplatesGridSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            Failed to load templates. Please try again.
          </div>
        </CardContent>
      </Card>
    );
  }

  const filteredTemplates = selectedCategory
    ? templates.filter((t) => t.category === selectedCategory)
    : templates;

  if (filteredTemplates.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground py-8">
            <FileSearch className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No templates available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {filteredTemplates.map((template) => (
        <TemplateCard
          key={template.name}
          template={template}
          onClick={() => onTemplateSelect?.(template)}
        />
      ))}
    </div>
  );
}

interface TemplateCardProps {
  template: OsintTemplate;
  onClick?: () => void;
}

function TemplateCard({ template, onClick }: TemplateCardProps) {
  const icon = categoryIcons[template.category] || <FileSearch className="h-5 w-5" />;

  return (
    <Card
      className={`transition-all hover:shadow-md ${onClick ? 'cursor-pointer hover:border-primary/50' : ''}`}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className="rounded-md bg-primary/10 p-2 text-primary">{icon}</div>
            <div>
              <CardTitle className="text-base">{template.name}</CardTitle>
              <Badge variant="outline" className="mt-1 text-xs">
                {getCategoryLabel(template.category)}
              </Badge>
            </div>
          </div>
          {onClick && <ChevronRight className="h-5 w-5 text-muted-foreground" />}
        </div>
      </CardHeader>
      <CardContent>
        <CardDescription className="line-clamp-2 mb-3">
          {template.description}
        </CardDescription>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>~{template.estimated_runtime_seconds}s</span>
          </div>
          <span>{template.parameters.length} parameters</span>
        </div>
        {template.tags && template.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {template.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
            {template.tags.length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{template.tags.length - 3}
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TemplatesGridSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Skeleton className="h-10 w-10 rounded-md" />
              <div>
                <Skeleton className="h-5 w-32 mb-1" />
                <Skeleton className="h-4 w-20" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-full mb-1" />
            <Skeleton className="h-4 w-3/4 mb-3" />
            <div className="flex justify-between">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-3 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default TemplatesGrid;
