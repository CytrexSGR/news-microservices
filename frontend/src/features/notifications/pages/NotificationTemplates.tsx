/**
 * NotificationTemplates Page
 *
 * Admin page for managing notification templates.
 * Includes template list, preview, test, and send functionality.
 */

import { useState } from 'react';
import { FileText, Plus, Send } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TemplateList } from '../components/templates/TemplateList';
import { TemplateTester } from '../components/templates/TemplateTester';
import { SendNotificationForm } from '../components/templates/SendNotificationForm';
import type { NotificationTemplate } from '../types';

export function NotificationTemplates() {
  const [selectedTemplate, setSelectedTemplate] = useState<NotificationTemplate | null>(null);
  const [activeTab, setActiveTab] = useState<'list' | 'test' | 'send'>('list');

  const handleEdit = (template: NotificationTemplate) => {
    // TODO: Implement template editor modal/page
    console.log('Edit template:', template);
  };

  const handleTest = (template: NotificationTemplate) => {
    setSelectedTemplate(template);
    setActiveTab('test');
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="h-6 w-6" />
            Notification Templates
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage email, webhook, and push notification templates
          </p>
        </div>
        <div className="flex gap-2">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Template
          </Button>
        </div>
      </div>

      {/* Main content */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
        <TabsList>
          <TabsTrigger value="list" className="gap-2">
            <FileText className="h-4 w-4" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="test" className="gap-2">
            <Send className="h-4 w-4" />
            Test
          </TabsTrigger>
          <TabsTrigger value="send" className="gap-2">
            <Send className="h-4 w-4" />
            Send Manual
          </TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="mt-4">
          <TemplateList
            onEdit={handleEdit}
            onTest={handleTest}
          />
        </TabsContent>

        <TabsContent value="test" className="mt-4">
          <div className="grid gap-6 lg:grid-cols-2">
            <TemplateTester template={selectedTemplate ?? undefined} />
            <div className="space-y-4">
              <div className="p-4 border rounded-lg bg-muted/30">
                <h3 className="font-medium mb-2">How to Test Templates</h3>
                <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
                  <li>Select a template from the dropdown or click "Test" in the template list</li>
                  <li>Enter the recipient address (email, webhook URL, or device token)</li>
                  <li>Modify the test data JSON to customize variable values</li>
                  <li>Click "Send Test Notification" to verify delivery</li>
                </ol>
              </div>
              <div className="p-4 border rounded-lg border-yellow-500/50 bg-yellow-50/50 dark:bg-yellow-950/20">
                <h3 className="font-medium mb-2 text-yellow-700 dark:text-yellow-400">
                  Important Note
                </h3>
                <p className="text-sm text-muted-foreground">
                  Test notifications are sent to real recipients. Make sure to use
                  test addresses that you control to avoid sending notifications to
                  actual users.
                </p>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="send" className="mt-4">
          <div className="grid gap-6 lg:grid-cols-2">
            <SendNotificationForm />
            <div className="space-y-4">
              <div className="p-4 border rounded-lg bg-muted/30">
                <h3 className="font-medium mb-2">Sending Manual Notifications</h3>
                <div className="text-sm text-muted-foreground space-y-3">
                  <div>
                    <strong>Templated Notifications:</strong>
                    <p className="mt-1">
                      Use predefined templates with variable substitution.
                      Select a template, provide the user ID and any required
                      template variables.
                    </p>
                  </div>
                  <div>
                    <strong>Ad-hoc Notifications:</strong>
                    <p className="mt-1">
                      Send custom one-off notifications without a template.
                      Useful for announcements or personalized messages.
                    </p>
                  </div>
                </div>
              </div>
              <div className="p-4 border rounded-lg border-blue-500/50 bg-blue-50/50 dark:bg-blue-950/20">
                <h3 className="font-medium mb-2 text-blue-700 dark:text-blue-400">
                  Best Practices
                </h3>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>Use templates for recurring notification types</li>
                  <li>Test templates before sending to users</li>
                  <li>Include unsubscribe links in marketing emails</li>
                  <li>Respect user preferences and quiet hours</li>
                </ul>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
