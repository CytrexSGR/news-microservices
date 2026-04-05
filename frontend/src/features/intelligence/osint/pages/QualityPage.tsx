/**
 * QualityPage - Graph Quality Analysis Page
 *
 * Page for viewing knowledge graph quality metrics
 */
import { Link } from 'react-router-dom';
import { ArrowLeft, Activity } from 'lucide-react';
import { GraphQualityReport } from '../components/GraphQualityReport';

export function QualityPage() {
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
            <Activity className="h-6 w-6" />
            Graph Quality
          </h1>
          <p className="text-muted-foreground">
            Knowledge graph quality metrics and recommendations
          </p>
        </div>
      </div>

      {/* Graph Quality Report */}
      <GraphQualityReport />
    </div>
  );
}

export default QualityPage;
