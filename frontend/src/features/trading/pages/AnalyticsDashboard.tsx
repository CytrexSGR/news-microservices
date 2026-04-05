import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Construction, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';

/**
 * Analytics Dashboard - Under Construction
 *
 * This page previously connected to execution-service (Port 8120) for strategy
 * performance leaderboard data. The service has been archived.
 *
 * Strategy analytics will be rebuilt as part of the prediction-service refactoring.
 *
 * Archived: 2025-12-28
 * See: services/prediction-service/REFACTORING_PROMPT.md for the rebuild plan
 */
export default function AnalyticsDashboard() {
  return (
    <div className="container mx-auto p-6">
      <Card className="max-w-2xl mx-auto">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-yellow-100 dark:bg-yellow-900/30 rounded-full">
              <Construction className="h-12 w-12 text-yellow-600 dark:text-yellow-400" />
            </div>
          </div>
          <CardTitle className="text-2xl">Analytics Dashboard - Under Construction</CardTitle>
          <CardDescription className="text-base mt-2">
            Strategy performance analytics are being rebuilt as part of the prediction-service refactoring.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <h3 className="font-semibold">Previously available:</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Multi-Strategy Arena leaderboard</li>
              <li>• Real-time P&L tracking by strategy</li>
              <li>• Win rate and profit factor metrics</li>
              <li>• Strategy comparison charts</li>
            </ul>
          </div>

          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <h3 className="font-semibold">For backtesting analytics, use:</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• ML Lab Backtest results</li>
              <li>• Strategy Lab Walk-Forward validation</li>
            </ul>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/trading/ml-lab">
              <Button variant="default">
                Go to ML Lab
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link to="/trading/strategy-lab">
              <Button variant="outline">
                Go to Strategy Lab
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>

          <p className="text-xs text-center text-muted-foreground">
            Archived: 2025-12-28 • Rebuild in progress
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
