/**
 * CreateInstancePage - Create New Instance Page
 *
 * Page for creating a new OSINT monitoring instance
 */
import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Plus, FileSearch } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { CreateInstanceForm } from '../components/CreateInstanceForm';
import { TemplatesGrid } from '../components/TemplatesGrid';
import type { OsintTemplate } from '../types/osint.types';

export function CreateInstancePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const templateFromUrl = searchParams.get('template');

  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(
    templateFromUrl ? decodeURIComponent(templateFromUrl) : null
  );

  const handleTemplateSelect = (template: OsintTemplate) => {
    setSelectedTemplate(template.name);
  };

  const handleSuccess = (instanceId: string) => {
    navigate(`/intelligence/osint/instances/${instanceId}`);
  };

  const handleCancel = () => {
    if (selectedTemplate) {
      setSelectedTemplate(null);
    } else {
      navigate('/intelligence/osint/instances');
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/intelligence/osint/instances"
          className="rounded-md p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Plus className="h-6 w-6" />
            Create Instance
          </h1>
          <p className="text-muted-foreground">
            {selectedTemplate
              ? `Configure new instance from ${selectedTemplate}`
              : 'Select a template to create a new monitoring instance'}
          </p>
        </div>
      </div>

      {/* Template Selection or Form */}
      {selectedTemplate ? (
        <CreateInstanceForm
          templateName={selectedTemplate}
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      ) : (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileSearch className="h-5 w-5" />
                Select Template
              </CardTitle>
              <CardDescription>
                Choose a template to base your monitoring instance on
              </CardDescription>
            </CardHeader>
          </Card>
          <TemplatesGrid onTemplateSelect={handleTemplateSelect} />
        </div>
      )}
    </div>
  );
}

export default CreateInstancePage;
