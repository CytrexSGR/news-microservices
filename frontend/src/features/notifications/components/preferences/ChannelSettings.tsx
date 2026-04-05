/**
 * ChannelSettings Component
 *
 * Toggle switches for notification channels (Email, Webhook, Push).
 */

import { Mail, Webhook, Smartphone, ExternalLink, Loader2 } from 'lucide-react';
import { Switch } from '@/components/ui/Switch';
import { Label } from '@/components/ui/Label';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import { useNotificationPreferences, useToggleChannel, useUpdateNotificationPreferences } from '../../api';
import type { NotificationChannel } from '../../types';

interface ChannelSettingsProps {
  className?: string;
}

interface ChannelConfig {
  channel: 'email' | 'webhook' | 'push';
  label: string;
  description: string;
  icon: typeof Mail;
  requiresConfig: boolean;
}

const CHANNELS: ChannelConfig[] = [
  {
    channel: 'email',
    label: 'Email Notifications',
    description: 'Receive notifications via email to your registered address',
    icon: Mail,
    requiresConfig: false,
  },
  {
    channel: 'webhook',
    label: 'Webhook Notifications',
    description: 'Send notifications to a custom webhook URL',
    icon: Webhook,
    requiresConfig: true,
  },
  {
    channel: 'push',
    label: 'Push Notifications',
    description: 'Receive browser push notifications (requires permission)',
    icon: Smartphone,
    requiresConfig: true,
  },
];

export function ChannelSettings({ className }: ChannelSettingsProps) {
  const { data: preferences, isLoading } = useNotificationPreferences();
  const toggleChannel = useToggleChannel();
  const updatePreferences = useUpdateNotificationPreferences();

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Notification Channels</CardTitle>
          <CardDescription>Choose how you want to receive notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between p-4 rounded-lg border animate-pulse">
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-muted" />
                <div className="space-y-2">
                  <div className="h-4 w-32 bg-muted rounded" />
                  <div className="h-3 w-48 bg-muted rounded" />
                </div>
              </div>
              <div className="h-6 w-11 rounded-full bg-muted" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  const handleToggle = (channel: 'email' | 'webhook' | 'push', enabled: boolean) => {
    toggleChannel.mutate({ channel, enabled });
  };

  const handleWebhookUrlChange = (url: string) => {
    updatePreferences.mutate({ webhook_url: url });
  };

  const getChannelEnabled = (channel: 'email' | 'webhook' | 'push'): boolean => {
    if (!preferences) return false;
    switch (channel) {
      case 'email':
        return preferences.email_enabled;
      case 'webhook':
        return preferences.webhook_enabled;
      case 'push':
        return preferences.push_enabled;
      default:
        return false;
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Notification Channels</CardTitle>
        <CardDescription>Choose how you want to receive notifications</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {CHANNELS.map(({ channel, label, description, icon: Icon, requiresConfig }) => {
          const enabled = getChannelEnabled(channel);
          const isToggling = toggleChannel.isPending && toggleChannel.variables?.channel === channel;

          return (
            <div
              key={channel}
              className={cn(
                'p-4 rounded-lg border transition-colors',
                enabled ? 'border-primary/30 bg-primary/5' : 'border-border'
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div
                    className={cn(
                      'h-10 w-10 rounded-full flex items-center justify-center',
                      enabled ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <Label htmlFor={`${channel}-toggle`} className="text-base font-medium">
                      {label}
                    </Label>
                    <p className="text-sm text-muted-foreground">{description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isToggling && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                  <Switch
                    id={`${channel}-toggle`}
                    checked={enabled}
                    onCheckedChange={(checked) => handleToggle(channel, checked)}
                    disabled={isToggling}
                  />
                </div>
              </div>

              {/* Webhook URL config */}
              {channel === 'webhook' && enabled && (
                <div className="mt-4 ml-14">
                  <Label htmlFor="webhook-url" className="text-sm">
                    Webhook URL
                  </Label>
                  <div className="flex gap-2 mt-1.5">
                    <Input
                      id="webhook-url"
                      type="url"
                      placeholder="https://your-server.com/webhook"
                      defaultValue={preferences?.webhook_url || ''}
                      onBlur={(e) => handleWebhookUrlChange(e.target.value)}
                      className="flex-1"
                    />
                    <Button variant="outline" size="icon" title="Test webhook">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    We'll send POST requests to this URL for each notification
                  </p>
                </div>
              )}

              {/* Push notification config */}
              {channel === 'push' && enabled && (
                <div className="mt-4 ml-14">
                  <Button variant="outline" size="sm">
                    Request Browser Permission
                  </Button>
                  <p className="text-xs text-muted-foreground mt-1.5">
                    You need to allow browser notifications to receive push messages
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
