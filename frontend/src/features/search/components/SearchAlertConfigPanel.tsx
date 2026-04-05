/**
 * SearchAlertConfigPanel Component
 *
 * Panel for configuring search alerts including channel selection,
 * threshold configuration, and cooldown settings.
 */

import * as React from 'react';
import { useState, useCallback } from 'react';
import {
  Bell,
  Mail,
  Webhook,
  Bell as InAppBell,
  Send,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Settings2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Switch } from '@/components/ui/Switch';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import {
  useSearchAlertConfig,
  useConfigureSearchAlert,
  useTestSearchAlert,
} from '../api/useSearchAlerts';
import type { AlertChannelType, SearchAlertConfigRequest } from '../types/search.types';

interface SearchAlertConfigPanelProps {
  /** Saved search ID */
  savedSearchId: string;
  /** Saved search name (for display) */
  savedSearchName?: string;
  /** Called when configuration is saved */
  onSaved?: () => void;
  /** Additional CSS classes */
  className?: string;
}

// Channel configuration options
const CHANNELS: Array<{
  value: AlertChannelType;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  {
    value: 'email',
    label: 'Email',
    description: 'Receive alerts via email notification',
    icon: Mail,
  },
  {
    value: 'webhook',
    label: 'Webhook',
    description: 'Send alerts to a custom webhook URL',
    icon: Webhook,
  },
  {
    value: 'in_app',
    label: 'In-App',
    description: 'Show alerts in the notification center',
    icon: InAppBell,
  },
];

// Cooldown presets
const COOLDOWN_PRESETS = [
  { value: 15, label: '15 min' },
  { value: 30, label: '30 min' },
  { value: 60, label: '1 hour' },
  { value: 180, label: '3 hours' },
  { value: 360, label: '6 hours' },
  { value: 720, label: '12 hours' },
  { value: 1440, label: '24 hours' },
];

export function SearchAlertConfigPanel({
  savedSearchId,
  savedSearchName,
  onSaved,
  className,
}: SearchAlertConfigPanelProps) {
  const { data: existingConfig, isLoading } = useSearchAlertConfig(savedSearchId);
  const { mutate: configure, isPending: isSaving } = useConfigureSearchAlert();
  const { mutate: testAlert, isPending: isTesting } = useTestSearchAlert();

  // Form state
  const [enabled, setEnabled] = useState(existingConfig?.enabled ?? true);
  const [alertType, setAlertType] = useState<AlertChannelType>(
    existingConfig?.alert_type || 'in_app'
  );
  const [threshold, setThreshold] = useState(existingConfig?.threshold || 5);
  const [cooldownMinutes, setCooldownMinutes] = useState(
    existingConfig?.cooldown_minutes || 60
  );
  const [webhookUrl, setWebhookUrl] = useState(existingConfig?.webhook_url || '');
  const [email, setEmail] = useState(existingConfig?.email || '');

  // Update form when data loads
  React.useEffect(() => {
    if (existingConfig) {
      setEnabled(existingConfig.enabled);
      setAlertType(existingConfig.alert_type);
      setThreshold(existingConfig.threshold);
      setCooldownMinutes(existingConfig.cooldown_minutes);
      setWebhookUrl(existingConfig.webhook_url || '');
      setEmail(existingConfig.email || '');
    }
  }, [existingConfig]);

  const handleSave = useCallback(() => {
    // Validate webhook URL if selected
    if (alertType === 'webhook' && !webhookUrl.trim()) {
      toast.error('Please enter a webhook URL');
      return;
    }

    // Validate URL format
    if (alertType === 'webhook') {
      try {
        new URL(webhookUrl);
      } catch {
        toast.error('Invalid webhook URL format');
        return;
      }
    }

    const config: SearchAlertConfigRequest = {
      alert_type: alertType,
      threshold,
      cooldown_minutes: cooldownMinutes,
      enabled,
      webhook_url: alertType === 'webhook' ? webhookUrl : undefined,
      email: alertType === 'email' && email ? email : undefined,
    };

    configure(
      { savedSearchId, config },
      {
        onSuccess: () => {
          onSaved?.();
        },
      }
    );
  }, [
    savedSearchId,
    alertType,
    threshold,
    cooldownMinutes,
    enabled,
    webhookUrl,
    email,
    configure,
    onSaved,
  ]);

  const handleTest = useCallback(() => {
    testAlert(savedSearchId);
  }, [savedSearchId, testAlert]);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="py-8 text-center">
          <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground mt-2">Loading configuration...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Alert Configuration
            </CardTitle>
            {savedSearchName && (
              <CardDescription>
                Configure alerts for &quot;{savedSearchName}&quot;
              </CardDescription>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="alert-enabled" className="text-sm">
              Enabled
            </Label>
            <Switch
              id="alert-enabled"
              checked={enabled}
              onCheckedChange={setEnabled}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Channel Selection */}
        <div className="space-y-3">
          <Label className="text-sm font-medium">Alert Channel</Label>
          <RadioGroup
            value={alertType}
            onValueChange={(value) => setAlertType(value as AlertChannelType)}
            className="grid gap-3"
          >
            {CHANNELS.map((channel) => {
              const Icon = channel.icon;
              return (
                <label
                  key={channel.value}
                  className={cn(
                    'flex items-start gap-3 rounded-lg border p-4 cursor-pointer transition-colors',
                    alertType === channel.value
                      ? 'border-primary bg-primary/5'
                      : 'hover:bg-muted/50'
                  )}
                >
                  <RadioGroupItem
                    value={channel.value}
                    id={`channel-${channel.value}`}
                    className="mt-0.5"
                  />
                  <Icon
                    className={cn(
                      'h-5 w-5 shrink-0',
                      alertType === channel.value
                        ? 'text-primary'
                        : 'text-muted-foreground'
                    )}
                  />
                  <div className="space-y-0.5">
                    <div className="font-medium text-sm">{channel.label}</div>
                    <div className="text-xs text-muted-foreground">
                      {channel.description}
                    </div>
                  </div>
                </label>
              );
            })}
          </RadioGroup>
        </div>

        {/* Channel-specific configuration */}
        {alertType === 'webhook' && (
          <div className="space-y-2">
            <Label htmlFor="webhook-url">Webhook URL</Label>
            <Input
              id="webhook-url"
              type="url"
              placeholder="https://your-server.com/webhook"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              We&apos;ll send a POST request with alert details in JSON format.
            </p>
          </div>
        )}

        {alertType === 'email' && (
          <div className="space-y-2">
            <Label htmlFor="email">Email Address (optional)</Label>
            <Input
              id="email"
              type="email"
              placeholder="Override default email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Leave empty to use your account email.
            </p>
          </div>
        )}

        <Separator />

        {/* Threshold Configuration */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Result Threshold</Label>
              <p className="text-xs text-muted-foreground">
                Minimum new results to trigger alert
              </p>
            </div>
            <span className="text-2xl font-bold tabular-nums">{threshold}</span>
          </div>
          <Slider
            value={[threshold]}
            onValueChange={([value]) => setThreshold(value)}
            min={1}
            max={50}
            step={1}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>1 result</span>
            <span>50 results</span>
          </div>
        </div>

        <Separator />

        {/* Cooldown Configuration */}
        <div className="space-y-3">
          <div>
            <Label className="text-sm font-medium">Cooldown Period</Label>
            <p className="text-xs text-muted-foreground">
              Minimum time between alerts
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {COOLDOWN_PRESETS.map((preset) => (
              <Button
                key={preset.value}
                variant={cooldownMinutes === preset.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCooldownMinutes(preset.value)}
              >
                {preset.label}
              </Button>
            ))}
          </div>
        </div>

        <Separator />

        {/* Summary */}
        <Alert>
          <Settings2 className="h-4 w-4" />
          <AlertTitle>Alert Summary</AlertTitle>
          <AlertDescription className="text-sm">
            {enabled ? (
              <>
                You will receive <strong>{alertType}</strong> alerts when there are{' '}
                <strong>{threshold} or more</strong> new results, with at least{' '}
                <strong>
                  {cooldownMinutes >= 60
                    ? `${Math.floor(cooldownMinutes / 60)} hour${cooldownMinutes >= 120 ? 's' : ''}`
                    : `${cooldownMinutes} minutes`}
                </strong>{' '}
                between alerts.
              </>
            ) : (
              'Alerts are currently disabled.'
            )}
          </AlertDescription>
        </Alert>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2">
          <Button
            variant="outline"
            onClick={handleTest}
            disabled={isTesting || !enabled}
          >
            {isTesting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Test Alert
              </>
            )}
          </Button>

          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Save Configuration
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
