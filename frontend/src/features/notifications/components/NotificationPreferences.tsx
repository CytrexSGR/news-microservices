/**
 * NotificationPreferences Component
 *
 * Settings panel for managing notification preferences.
 */

import { useState } from 'react';
import { Save, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Switch } from '@/components/ui/Switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { useNotificationPreferences, useUpdateNotificationPreferences } from '../api';
import type { NotificationPreferencesUpdate } from '../types';

export function NotificationPreferences() {
  const { data: preferences, isLoading } = useNotificationPreferences();
  const updateMutation = useUpdateNotificationPreferences();

  const [formState, setFormState] = useState<NotificationPreferencesUpdate>({});
  const [webhookUrl, setWebhookUrl] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  // Sync form state when preferences load
  if (preferences && !isDirty && Object.keys(formState).length === 0) {
    setFormState({
      email_enabled: preferences.email_enabled,
      webhook_enabled: preferences.webhook_enabled,
      push_enabled: preferences.push_enabled,
    });
    setWebhookUrl(preferences.webhook_url || '');
  }

  const handleToggle = (field: keyof NotificationPreferencesUpdate) => (checked: boolean) => {
    setFormState((prev) => ({ ...prev, [field]: checked }));
    setIsDirty(true);
  };

  const handleWebhookUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setWebhookUrl(e.target.value);
    setIsDirty(true);
  };

  const handleSave = () => {
    const updates: NotificationPreferencesUpdate = {
      ...formState,
    };

    if (formState.webhook_enabled && webhookUrl) {
      updates.webhook_url = webhookUrl;
    }

    updateMutation.mutate(updates, {
      onSuccess: () => {
        setIsDirty(false);
      },
    });
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-72" />
        </CardHeader>
        <CardContent className="space-y-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="space-y-1">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
              <Skeleton className="h-6 w-12 rounded-full" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Notification Preferences</CardTitle>
        <CardDescription>
          Choose how you want to receive notifications
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Email Notifications */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="email-toggle" className="text-base">
              Email Notifications
            </Label>
            <p className="text-sm text-muted-foreground">
              Receive notifications via email
            </p>
          </div>
          <Switch
            id="email-toggle"
            checked={formState.email_enabled ?? preferences?.email_enabled ?? true}
            onCheckedChange={handleToggle('email_enabled')}
          />
        </div>

        {/* Webhook Notifications */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="webhook-toggle" className="text-base">
                Webhook Notifications
              </Label>
              <p className="text-sm text-muted-foreground">
                Send notifications to a webhook URL
              </p>
            </div>
            <Switch
              id="webhook-toggle"
              checked={formState.webhook_enabled ?? preferences?.webhook_enabled ?? false}
              onCheckedChange={handleToggle('webhook_enabled')}
            />
          </div>

          {(formState.webhook_enabled ?? preferences?.webhook_enabled) && (
            <div className="space-y-2 pl-4 border-l-2 border-border">
              <Label htmlFor="webhook-url">Webhook URL</Label>
              <Input
                id="webhook-url"
                type="url"
                placeholder="https://example.com/webhook"
                value={webhookUrl}
                onChange={handleWebhookUrlChange}
              />
              <p className="text-xs text-muted-foreground">
                Notifications will be sent as POST requests with JSON payload
              </p>
            </div>
          )}
        </div>

        {/* Push Notifications */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="push-toggle" className="text-base">
              Push Notifications
            </Label>
            <p className="text-sm text-muted-foreground">
              Browser push notifications (coming soon)
            </p>
          </div>
          <Switch
            id="push-toggle"
            checked={formState.push_enabled ?? preferences?.push_enabled ?? false}
            onCheckedChange={handleToggle('push_enabled')}
            disabled
          />
        </div>

        {/* Save Button */}
        <div className="pt-4 border-t border-border">
          <Button
            onClick={handleSave}
            disabled={!isDirty || updateMutation.isPending}
            className="w-full sm:w-auto"
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Preferences
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
