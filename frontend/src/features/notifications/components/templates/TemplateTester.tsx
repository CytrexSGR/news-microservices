/**
 * TemplateTester Component
 *
 * Form to test notification templates by sending test messages.
 */

import { useState } from 'react';
import { Send, Loader2, CheckCircle, XCircle, Info } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { useTestNotification, useNotificationTemplates } from '../../api';
import type { NotificationChannel, NotificationTemplate } from '../../types';

interface TemplateTesterProps {
  template?: NotificationTemplate;
  className?: string;
}

export function TemplateTester({ template: initialTemplate, className }: TemplateTesterProps) {
  const { data: templatesData } = useNotificationTemplates();
  const testNotification = useTestNotification();

  const [selectedTemplate, setSelectedTemplate] = useState<string>(
    initialTemplate?.name || ''
  );
  const [channel, setChannel] = useState<NotificationChannel>(
    initialTemplate?.channel || 'email'
  );
  const [recipient, setRecipient] = useState('');
  const [testData, setTestData] = useState<string>('{}');
  const [result, setResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const templates = templatesData?.templates ?? [];
  const currentTemplate = templates.find((t) => t.name === selectedTemplate);

  const handleTest = async () => {
    setResult(null);

    try {
      let parsedTestData = {};
      if (testData.trim()) {
        parsedTestData = JSON.parse(testData);
      }

      const response = await testNotification.mutateAsync({
        channel,
        recipient,
        template_name: selectedTemplate || undefined,
        test_data: parsedTestData,
      });

      setResult({
        success: response.success,
        message: response.message || 'Test notification sent successfully',
      });
    } catch (error) {
      setResult({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to send test notification',
      });
    }
  };

  const handleTemplateChange = (templateName: string) => {
    setSelectedTemplate(templateName);
    const template = templates.find((t) => t.name === templateName);
    if (template) {
      setChannel(template.channel);
      // Generate sample test data
      const sampleData: Record<string, string> = {};
      template.variables.forEach((v) => {
        sampleData[v] = `Sample ${v}`;
      });
      setTestData(JSON.stringify(sampleData, null, 2));
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-5 w-5" />
          Test Notification
        </CardTitle>
        <CardDescription>
          Send a test notification to verify template rendering and delivery
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Template selection */}
        <div>
          <Label htmlFor="template">Template</Label>
          <Select value={selectedTemplate} onValueChange={handleTemplateChange}>
            <SelectTrigger id="template" className="mt-1.5">
              <SelectValue placeholder="Select a template" />
            </SelectTrigger>
            <SelectContent>
              {templates.map((t) => (
                <SelectItem key={t.id} value={t.name}>
                  {t.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Channel */}
        <div>
          <Label htmlFor="channel">Channel</Label>
          <Select value={channel} onValueChange={(v) => setChannel(v as NotificationChannel)}>
            <SelectTrigger id="channel" className="mt-1.5">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="email">Email</SelectItem>
              <SelectItem value="webhook">Webhook</SelectItem>
              <SelectItem value="push">Push</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Recipient */}
        <div>
          <Label htmlFor="recipient">
            Recipient
            <span className="text-muted-foreground text-xs ml-1">
              ({channel === 'email' ? 'Email address' : channel === 'webhook' ? 'Webhook URL' : 'Device token'})
            </span>
          </Label>
          <Input
            id="recipient"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder={
              channel === 'email'
                ? 'test@example.com'
                : channel === 'webhook'
                ? 'https://...'
                : 'device-token'
            }
            className="mt-1.5"
          />
        </div>

        {/* Test data */}
        <div>
          <Label htmlFor="test-data">
            Test Data (JSON)
            {currentTemplate && currentTemplate.variables.length > 0 && (
              <span className="text-muted-foreground text-xs ml-1">
                Variables: {currentTemplate.variables.join(', ')}
              </span>
            )}
          </Label>
          <Textarea
            id="test-data"
            value={testData}
            onChange={(e) => setTestData(e.target.value)}
            placeholder="{}"
            className="mt-1.5 font-mono text-sm"
            rows={6}
          />
        </div>

        {/* Info */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            This will send a real notification to the specified recipient. Make sure the recipient
            is a valid test address you control.
          </AlertDescription>
        </Alert>

        {/* Result */}
        {result && (
          <Alert variant={result.success ? 'default' : 'destructive'}>
            {result.success ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            <AlertDescription>{result.message}</AlertDescription>
          </Alert>
        )}

        {/* Submit */}
        <Button
          onClick={handleTest}
          disabled={!recipient || testNotification.isPending}
          className="w-full"
        >
          {testNotification.isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Sending...
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Send Test Notification
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
