/**
 * SendNotificationForm Component
 *
 * Form for sending manual notifications (templated or ad-hoc).
 */

import { useState } from 'react';
import { Send, Loader2, CheckCircle, XCircle, Mail } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useSendNotification, useSendAdhocNotification, useNotificationTemplates } from '../../api';
import type { NotificationChannel } from '../../types';

interface SendNotificationFormProps {
  className?: string;
}

export function SendNotificationForm({ className }: SendNotificationFormProps) {
  const { data: templatesData } = useNotificationTemplates();
  const sendNotification = useSendNotification();
  const sendAdhocNotification = useSendAdhocNotification();

  // Templated form state
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [userId, setUserId] = useState('');
  const [channel, setChannel] = useState<NotificationChannel>('email');
  const [templateVariables, setTemplateVariables] = useState<string>('{}');

  // Ad-hoc form state
  const [adhocRecipient, setAdhocRecipient] = useState('');
  const [adhocSubject, setAdhocSubject] = useState('');
  const [adhocBody, setAdhocBody] = useState('');
  const [bodyFormat, setBodyFormat] = useState<'plain' | 'html' | 'markdown'>('markdown');

  const [result, setResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const templates = templatesData?.templates ?? [];
  const currentTemplate = templates.find((t) => t.name === selectedTemplate);

  const handleSendTemplated = async () => {
    setResult(null);

    try {
      let parsedVariables = {};
      if (templateVariables.trim()) {
        parsedVariables = JSON.parse(templateVariables);
      }

      await sendNotification.mutateAsync({
        user_id: userId,
        channel,
        template_name: selectedTemplate,
        template_variables: parsedVariables,
        content: '', // Required but template will provide content
      });

      setResult({
        success: true,
        message: 'Notification sent successfully',
      });
    } catch (error) {
      setResult({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to send notification',
      });
    }
  };

  const handleSendAdhoc = async () => {
    setResult(null);

    try {
      await sendAdhocNotification.mutateAsync({
        recipient: adhocRecipient,
        subject: adhocSubject,
        body: adhocBody,
        body_format: bodyFormat,
      });

      setResult({
        success: true,
        message: 'Notification sent successfully',
      });
    } catch (error) {
      setResult({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to send notification',
      });
    }
  };

  const handleTemplateChange = (templateName: string) => {
    setSelectedTemplate(templateName);
    const template = templates.find((t) => t.name === templateName);
    if (template) {
      setChannel(template.channel);
      const sampleVars: Record<string, string> = {};
      template.variables.forEach((v) => {
        sampleVars[v] = '';
      });
      setTemplateVariables(JSON.stringify(sampleVars, null, 2));
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mail className="h-5 w-5" />
          Send Notification
        </CardTitle>
        <CardDescription>
          Send notifications manually using templates or custom content
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="templated">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="templated">Use Template</TabsTrigger>
            <TabsTrigger value="adhoc">Ad-hoc</TabsTrigger>
          </TabsList>

          {/* Templated notification */}
          <TabsContent value="templated" className="space-y-4 mt-4">
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

            <div>
              <Label htmlFor="user-id">User ID</Label>
              <Input
                id="user-id"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="Enter user ID"
                className="mt-1.5"
              />
            </div>

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

            {currentTemplate && currentTemplate.variables.length > 0 && (
              <div>
                <Label htmlFor="variables">
                  Template Variables (JSON)
                  <span className="text-muted-foreground text-xs ml-1">
                    {currentTemplate.variables.join(', ')}
                  </span>
                </Label>
                <Textarea
                  id="variables"
                  value={templateVariables}
                  onChange={(e) => setTemplateVariables(e.target.value)}
                  className="mt-1.5 font-mono text-sm"
                  rows={4}
                />
              </div>
            )}

            <Button
              onClick={handleSendTemplated}
              disabled={!selectedTemplate || !userId || sendNotification.isPending}
              className="w-full"
            >
              {sendNotification.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Send Notification
                </>
              )}
            </Button>
          </TabsContent>

          {/* Ad-hoc notification */}
          <TabsContent value="adhoc" className="space-y-4 mt-4">
            <div>
              <Label htmlFor="adhoc-recipient">Recipient Email</Label>
              <Input
                id="adhoc-recipient"
                type="email"
                value={adhocRecipient}
                onChange={(e) => setAdhocRecipient(e.target.value)}
                placeholder="recipient@example.com"
                className="mt-1.5"
              />
            </div>

            <div>
              <Label htmlFor="adhoc-subject">Subject</Label>
              <Input
                id="adhoc-subject"
                value={adhocSubject}
                onChange={(e) => setAdhocSubject(e.target.value)}
                placeholder="Notification subject"
                className="mt-1.5"
              />
            </div>

            <div>
              <div className="flex items-center justify-between">
                <Label htmlFor="adhoc-body">Body</Label>
                <Select
                  value={bodyFormat}
                  onValueChange={(v) => setBodyFormat(v as typeof bodyFormat)}
                >
                  <SelectTrigger className="w-[120px] h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="plain">Plain Text</SelectItem>
                    <SelectItem value="markdown">Markdown</SelectItem>
                    <SelectItem value="html">HTML</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Textarea
                id="adhoc-body"
                value={adhocBody}
                onChange={(e) => setAdhocBody(e.target.value)}
                placeholder="Write your message..."
                className="mt-1.5"
                rows={8}
              />
            </div>

            <Button
              onClick={handleSendAdhoc}
              disabled={
                !adhocRecipient || !adhocSubject || !adhocBody || sendAdhocNotification.isPending
              }
              className="w-full"
            >
              {sendAdhocNotification.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Send Ad-hoc Notification
                </>
              )}
            </Button>
          </TabsContent>
        </Tabs>

        {/* Result */}
        {result && (
          <Alert variant={result.success ? 'default' : 'destructive'} className="mt-4">
            {result.success ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            <AlertDescription>{result.message}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
