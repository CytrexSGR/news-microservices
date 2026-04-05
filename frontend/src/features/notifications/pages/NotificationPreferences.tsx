/**
 * NotificationPreferences Page
 *
 * User preferences page for notification channels, categories, and quiet hours.
 */

import { useState } from 'react';
import { Settings, Bell, Clock, Tag, Save, Loader2, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ChannelSettings } from '../components/preferences/ChannelSettings';
import { CategorySettings } from '../components/preferences/CategorySettings';
import { QuietHoursSettings } from '../components/preferences/QuietHoursSettings';
import { useNotificationPreferences, useUpdateNotificationPreferences } from '../api';
import type { NotificationPreferences } from '../types';

export function NotificationPreferences() {
  const { data: preferences, isLoading, error } = useNotificationPreferences();
  const updatePreferences = useUpdateNotificationPreferences();

  const [localPreferences, setLocalPreferences] = useState<Partial<NotificationPreferences>>({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const mergedPreferences: NotificationPreferences = {
    ...preferences,
    ...localPreferences,
  } as NotificationPreferences;

  const handlePreferenceChange = (key: keyof NotificationPreferences, value: unknown) => {
    setLocalPreferences((prev) => ({
      ...prev,
      [key]: value,
    }));
    setHasUnsavedChanges(true);
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    try {
      await updatePreferences.mutateAsync(localPreferences);
      setHasUnsavedChanges(false);
      setSaveSuccess(true);
      setLocalPreferences({});
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      // Error is handled by the mutation
    }
  };

  const handleReset = () => {
    setLocalPreferences({});
    setHasUnsavedChanges(false);
  };

  if (error) {
    return (
      <div className="container mx-auto py-6">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-8">
              <p className="text-destructive mb-4">Failed to load notification preferences</p>
              <Button variant="outline" onClick={() => window.location.reload()}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Settings className="h-6 w-6" />
            Notification Preferences
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure how and when you receive notifications
          </p>
        </div>
        <div className="flex gap-2">
          {hasUnsavedChanges && (
            <Button variant="outline" onClick={handleReset}>
              Reset
            </Button>
          )}
          <Button
            onClick={handleSave}
            disabled={!hasUnsavedChanges || updatePreferences.isPending}
          >
            {updatePreferences.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Success message */}
      {saveSuccess && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>Your preferences have been saved successfully.</AlertDescription>
        </Alert>
      )}

      {/* Unsaved changes indicator */}
      {hasUnsavedChanges && (
        <Alert>
          <AlertDescription>
            You have unsaved changes. Click "Save Changes" to apply them.
          </AlertDescription>
        </Alert>
      )}

      {/* Settings tabs */}
      <Tabs defaultValue="channels" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 lg:w-auto lg:grid-cols-none">
          <TabsTrigger value="channels" className="gap-2">
            <Bell className="h-4 w-4 hidden sm:inline" />
            Channels
          </TabsTrigger>
          <TabsTrigger value="categories" className="gap-2">
            <Tag className="h-4 w-4 hidden sm:inline" />
            Categories
          </TabsTrigger>
          <TabsTrigger value="quiet-hours" className="gap-2">
            <Clock className="h-4 w-4 hidden sm:inline" />
            Quiet Hours
          </TabsTrigger>
        </TabsList>

        <TabsContent value="channels" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Notification Channels</CardTitle>
              <CardDescription>
                Choose which channels can be used to send you notifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ChannelSettings
                preferences={mergedPreferences}
                isLoading={isLoading}
                onPreferenceChange={handlePreferenceChange}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="categories" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Notification Categories</CardTitle>
              <CardDescription>
                Customize notifications by category and importance level
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CategorySettings
                preferences={mergedPreferences}
                isLoading={isLoading}
                onPreferenceChange={handlePreferenceChange}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="quiet-hours" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Quiet Hours</CardTitle>
              <CardDescription>
                Set times when non-urgent notifications will be silenced
              </CardDescription>
            </CardHeader>
            <CardContent>
              <QuietHoursSettings
                preferences={mergedPreferences}
                isLoading={isLoading}
                onPreferenceChange={handlePreferenceChange}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
