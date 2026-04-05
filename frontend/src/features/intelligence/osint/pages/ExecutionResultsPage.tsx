/**
 * ExecutionResultsPage - Execution Results Page
 *
 * Page for viewing OSINT execution results
 */
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, FileJson, AlertCircle } from 'lucide-react';
import { ExecutionResultView } from '../components/ExecutionResultView';

export function ExecutionResultsPage() {
  const { executionId } = useParams<{ executionId: string }>();

  if (!executionId) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-semibold">Execution ID Not Provided</h2>
          <p className="text-muted-foreground mt-2">
            No execution ID was provided in the URL.
          </p>
          <Link
            to="/intelligence/osint/instances"
            className="text-primary hover:underline mt-4 inline-block"
          >
            Back to instances
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
          to="/intelligence/osint/instances"
          className="rounded-md p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileJson className="h-6 w-6" />
            Execution Results
          </h1>
          <p className="text-muted-foreground">
            Viewing results for execution {executionId.slice(0, 8)}...
          </p>
        </div>
      </div>

      {/* Execution Results */}
      <ExecutionResultView executionId={executionId} />
    </div>
  );
}

export default ExecutionResultsPage;
