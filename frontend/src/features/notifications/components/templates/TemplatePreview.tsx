/**
 * TemplatePreview Component
 *
 * Modal showing template preview with variable substitution.
 */

import { useState, useMemo } from 'react';
import { X, Code, Eye, Copy, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import type { NotificationTemplate } from '../../types';

interface TemplatePreviewProps {
  template: NotificationTemplate;
  onClose: () => void;
}

export function TemplatePreview({ template, onClose }: TemplatePreviewProps) {
  const [variables, setVariables] = useState<Record<string, string>>(() => {
    // Initialize with sample values
    const initial: Record<string, string> = {};
    template.variables.forEach((v) => {
      initial[v] = `{{${v}}}`;
    });
    return initial;
  });
  const [copied, setCopied] = useState(false);

  // Render template with variable substitution
  const renderedSubject = useMemo(() => {
    if (!template.subject) return '';
    let result = template.subject;
    Object.entries(variables).forEach(([key, value]) => {
      result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value);
    });
    return result;
  }, [template.subject, variables]);

  const renderedBody = useMemo(() => {
    let result = template.body;
    Object.entries(variables).forEach(([key, value]) => {
      result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value);
    });
    return result;
  }, [template.body, variables]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(template.body);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-3xl max-h-[90vh] bg-background rounded-lg shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h2 className="text-lg font-semibold">{template.name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className="capitalize">
                {template.channel}
              </Badge>
              {template.variables.length > 0 && (
                <span className="text-xs text-muted-foreground">
                  {template.variables.length} variable(s)
                </span>
              )}
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Variables sidebar */}
          {template.variables.length > 0 && (
            <div className="w-64 border-r p-4 overflow-y-auto bg-muted/30">
              <h3 className="font-medium mb-3">Variables</h3>
              <div className="space-y-3">
                {template.variables.map((variable) => (
                  <div key={variable}>
                    <Label htmlFor={variable} className="text-xs font-mono">
                      {`{{${variable}}}`}
                    </Label>
                    <Input
                      id={variable}
                      value={variables[variable] || ''}
                      onChange={(e) =>
                        setVariables((prev) => ({
                          ...prev,
                          [variable]: e.target.value,
                        }))
                      }
                      className="mt-1 text-sm"
                      placeholder={`Enter ${variable}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Preview area */}
          <div className="flex-1 overflow-hidden">
            <Tabs defaultValue="preview" className="h-full flex flex-col">
              <div className="border-b px-4">
                <TabsList className="h-11">
                  <TabsTrigger value="preview" className="gap-2">
                    <Eye className="h-4 w-4" />
                    Preview
                  </TabsTrigger>
                  <TabsTrigger value="source" className="gap-2">
                    <Code className="h-4 w-4" />
                    Source
                  </TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value="preview" className="flex-1 p-4 overflow-y-auto m-0">
                {/* Subject */}
                {template.subject && (
                  <div className="mb-4">
                    <Label className="text-xs text-muted-foreground">Subject</Label>
                    <div className="mt-1 p-3 rounded-lg border bg-muted/50 font-medium">
                      {renderedSubject}
                    </div>
                  </div>
                )}

                {/* Body */}
                <div>
                  <Label className="text-xs text-muted-foreground">Body</Label>
                  <div className="mt-1 p-4 rounded-lg border bg-white dark:bg-background min-h-[200px]">
                    {template.channel === 'email' ? (
                      <div
                        className="prose prose-sm max-w-none dark:prose-invert"
                        dangerouslySetInnerHTML={{ __html: renderedBody }}
                      />
                    ) : (
                      <pre className="whitespace-pre-wrap text-sm font-mono">
                        {renderedBody}
                      </pre>
                    )}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="source" className="flex-1 p-4 overflow-y-auto m-0">
                <div className="relative">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={handleCopy}
                  >
                    {copied ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-1 text-green-500" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-1" />
                        Copy
                      </>
                    )}
                  </Button>

                  {/* Subject source */}
                  {template.subject && (
                    <div className="mb-4">
                      <Label className="text-xs text-muted-foreground">Subject</Label>
                      <pre className="mt-1 p-3 rounded-lg border bg-muted/50 text-sm font-mono overflow-x-auto">
                        {template.subject}
                      </pre>
                    </div>
                  )}

                  {/* Body source */}
                  <div>
                    <Label className="text-xs text-muted-foreground">Body</Label>
                    <pre className="mt-1 p-4 rounded-lg border bg-muted/50 text-sm font-mono overflow-x-auto whitespace-pre-wrap">
                      {template.body}
                    </pre>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t p-4 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
