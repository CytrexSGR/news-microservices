/**
 * TemplateDetailsPage - Template Detail Page
 *
 * Page for viewing template details and creating instances
 */
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, FileSearch } from 'lucide-react';
import { TemplateDetailView } from '../components/TemplateDetailView';

export function TemplateDetailsPage() {
  const { templateName } = useParams<{ templateName: string }>();
  const navigate = useNavigate();

  const handleCreateInstance = () => {
    if (templateName) {
      navigate(`/intelligence/osint/instances/create?template=${encodeURIComponent(templateName)}`);
    }
  };

  if (!templateName) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12 text-muted-foreground">
          <FileSearch className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Template name not provided</p>
          <Link
            to="/intelligence/osint/templates"
            className="text-primary hover:underline mt-2 inline-block"
          >
            Browse templates
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/intelligence/osint/templates"
          className="rounded-md p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Template Details</h1>
          <p className="text-muted-foreground">
            View template configuration and parameters
          </p>
        </div>
      </div>

      {/* Template Detail */}
      <TemplateDetailView
        templateName={decodeURIComponent(templateName)}
        onCreateInstance={handleCreateInstance}
      />
    </div>
  );
}

export default TemplateDetailsPage;
