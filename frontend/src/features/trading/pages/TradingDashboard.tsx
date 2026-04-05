import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Construction, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';

/**
 * Trading Dashboard - Under Construction
 *
 * This page previously connected to execution-service (Port 8120) which has been archived.
 * Trading execution features will be rebuilt as part of the prediction-service refactoring.
 *
 * Archived: 2025-12-28
 * See: services/prediction-service/REFACTORING_PROMPT.md for the rebuild plan
 */
export default function TradingDashboard() {
  return (
    <div className="container mx-auto p-6">
      <Card className="max-w-2xl mx-auto">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-yellow-100 dark:bg-yellow-900/30 rounded-full">
              <Construction className="h-12 w-12 text-yellow-600 dark:text-yellow-400" />
            </div>
          </div>
          <CardTitle className="text-2xl">Trading Dashboard - Under Construction</CardTitle>
          <CardDescription className="text-base mt-2">
            The Trading Dashboard is being rebuilt as part of the prediction-service refactoring.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <h3 className="font-semibold">What's happening?</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• The execution-service has been archived</li>
              <li>• Trading features are being integrated into prediction-service</li>
              <li>• This includes position management, portfolio tracking, and kill switch</li>
            </ul>
          </div>

          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <h3 className="font-semibold">Available now:</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• ML Lab for model training and backtesting</li>
              <li>• Strategy Lab for strategy development</li>
              <li>• Market data via FMP service</li>
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
