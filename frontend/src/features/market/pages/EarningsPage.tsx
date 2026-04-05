/**
 * EarningsPage Component
 * Full earnings dashboard with calendar, table, and widgets
 */

import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calendar, List, TrendingUp, ArrowLeft } from 'lucide-react';
import {
  EarningsCalendar,
  EarningsCalendarTable,
  UpcomingEarningsWidget,
  EarningsSurprisesWidget,
} from '../components/earnings';
import type { EarningsEvent } from '../types/earnings.types';

interface EarningsPageProps {
  onBack?: () => void;
}

type ViewMode = 'calendar' | 'table';

export function EarningsPage({ onBack }: EarningsPageProps) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const viewMode = (searchParams.get('view') as ViewMode) || 'calendar';

  const setViewMode = (mode: ViewMode) => {
    setSearchParams((prev) => {
      prev.set('view', mode);
      return prev;
    });
  };

  const handleEventClick = (event: EarningsEvent) => {
    navigate(`/market/earnings/${event.symbol}`);
  };

  const handleSymbolClick = (symbol: string) => {
    navigate(`/market/earnings/${symbol}`);
  };

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate('/market');
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Earnings Calendar</h1>
            <p className="text-muted-foreground">
              Track upcoming earnings announcements and historical surprises
            </p>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Calendar/Table Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* View Toggle */}
          <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as ViewMode)}>
            <TabsList>
              <TabsTrigger value="calendar" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Calendar View
              </TabsTrigger>
              <TabsTrigger value="table" className="flex items-center gap-2">
                <List className="h-4 w-4" />
                Table View
              </TabsTrigger>
            </TabsList>

            <TabsContent value="calendar" className="mt-4">
              <EarningsCalendar onEventClick={handleEventClick} />
            </TabsContent>

            <TabsContent value="table" className="mt-4">
              <EarningsCalendarTable onEventClick={handleEventClick} />
            </TabsContent>
          </Tabs>

          {/* Recent Surprises */}
          <EarningsSurprisesWidget onSymbolClick={handleSymbolClick} />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Upcoming Earnings Widget */}
          <UpcomingEarningsWidget
            limit={10}
            showFilters
            onEventClick={handleEventClick}
            onViewAll={() => setViewMode('table')}
          />
        </div>
      </div>
    </div>
  );
}

export default EarningsPage;
