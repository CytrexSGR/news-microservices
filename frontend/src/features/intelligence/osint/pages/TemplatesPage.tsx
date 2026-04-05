/**
 * TemplatesPage - OSINT Templates List Page
 *
 * Page for browsing available OSINT templates
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileSearch, Filter } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { TemplatesGrid } from '../components/TemplatesGrid';
import type { OsintTemplate, OsintCategory } from '../types/osint.types';
import { getCategoryLabel } from '../types/osint.types';

const categories: OsintCategory[] = [
  'social_media',
  'domain_analysis',
  'threat_intelligence',
  'network_analysis',
  'financial',
  'person',
  'organization',
];

export function TemplatesPage() {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<OsintCategory | undefined>();

  const handleTemplateSelect = (template: OsintTemplate) => {
    navigate(`/intelligence/osint/templates/${encodeURIComponent(template.name)}`);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/intelligence/osint"
          className="rounded-md p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileSearch className="h-6 w-6" />
            OSINT Templates
          </h1>
          <p className="text-muted-foreground">
            Browse and select monitoring templates
          </p>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <button
          onClick={() => setSelectedCategory(undefined)}
          className={`rounded-full px-3 py-1 text-sm transition-colors ${
            !selectedCategory
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted hover:bg-muted-foreground/10'
          }`}
        >
          All
        </button>
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`rounded-full px-3 py-1 text-sm transition-colors ${
              selectedCategory === category
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted-foreground/10'
            }`}
          >
            {getCategoryLabel(category)}
          </button>
        ))}
      </div>

      {/* Templates Grid */}
      <TemplatesGrid
        selectedCategory={selectedCategory}
        onTemplateSelect={handleTemplateSelect}
      />
    </div>
  );
}

export default TemplatesPage;
