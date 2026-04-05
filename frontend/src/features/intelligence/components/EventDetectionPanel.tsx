import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/Label';
import { Switch } from '@/components/ui/Switch';
import { AlertCircle, Loader2, Search, User, Building2, MapPin, Tag, Clock } from 'lucide-react';
import { useEventDetection } from '../api/useEventDetection';

/**
 * Panel for real-time event detection from text content
 *
 * Features:
 * - Text input for article/content analysis
 * - Configurable keyword extraction
 * - Shows extracted entities (persons, organizations, locations)
 * - Shows extracted keywords
 * - Processing time indicator
 */
export function EventDetectionPanel() {
  const [text, setText] = useState('');
  const [includeKeywords, setIncludeKeywords] = useState(true);
  const [maxKeywords, setMaxKeywords] = useState(10);
  const { mutate, data, isPending, error, reset } = useEventDetection();

  const handleDetect = () => {
    if (!text.trim() || text.trim().length < 10) return;
    mutate({
      text: text.trim(),
      include_keywords: includeKeywords,
      max_keywords: maxKeywords,
    });
  };

  const handleClear = () => {
    setText('');
    setIncludeKeywords(true);
    setMaxKeywords(10);
    reset();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Event Detection
        </CardTitle>
        <CardDescription>
          Analyze text content to extract entities (persons, organizations, locations) and keywords
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Input Section */}
        <div className="space-y-3">
          <div>
            <Label htmlFor="text">Content to Analyze</Label>
            <Textarea
              id="text"
              placeholder="Paste article content or news text here (min. 10 characters)..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="mt-1 min-h-[120px]"
            />
            <p className="text-xs text-muted-foreground mt-1">
              {text.length} characters {text.length > 0 && text.length < 10 && '(min. 10 required)'}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <Switch
                id="includeKeywords"
                checked={includeKeywords}
                onCheckedChange={setIncludeKeywords}
              />
              <Label htmlFor="includeKeywords">Extract keywords</Label>
            </div>

            {includeKeywords && (
              <div>
                <Label htmlFor="maxKeywords">Max keywords</Label>
                <Input
                  id="maxKeywords"
                  type="number"
                  min={1}
                  max={50}
                  value={maxKeywords}
                  onChange={(e) => setMaxKeywords(parseInt(e.target.value) || 10)}
                  className="mt-1"
                />
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleDetect}
              disabled={isPending || text.trim().length < 10}
              className="flex-1"
            >
              {isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Detect Entities
                </>
              )}
            </Button>
            <Button variant="outline" onClick={handleClear}>
              Clear
            </Button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-lg">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error.message}</span>
          </div>
        )}

        {/* Results Section */}
        {data && (
          <div className="space-y-4 pt-4 border-t">
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-muted rounded-lg text-center">
                <p className="text-2xl font-bold text-primary">{data.entity_count}</p>
                <p className="text-xs text-muted-foreground">Entities Found</p>
              </div>
              <div className="p-3 bg-muted rounded-lg text-center">
                <p className="text-2xl font-bold text-primary">{data.keywords?.length || 0}</p>
                <p className="text-xs text-muted-foreground">Keywords</p>
              </div>
              <div className="p-3 bg-muted rounded-lg text-center">
                <div className="flex items-center justify-center gap-1">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <p className="text-lg font-bold">{data.processing_time_ms}ms</p>
                </div>
                <p className="text-xs text-muted-foreground">Processing Time</p>
              </div>
            </div>

            {/* Entities */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Extracted Entities</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Persons */}
                <div className="p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <User className="h-4 w-4 text-blue-500" />
                    <span className="text-xs font-medium">Persons</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {data.entities.persons.length > 0 ? (
                      data.entities.persons.map((person, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {person}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground">None detected</span>
                    )}
                  </div>
                </div>

                {/* Organizations */}
                <div className="p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Building2 className="h-4 w-4 text-purple-500" />
                    <span className="text-xs font-medium">Organizations</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {data.entities.organizations.length > 0 ? (
                      data.entities.organizations.map((org, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {org}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground">None detected</span>
                    )}
                  </div>
                </div>

                {/* Locations */}
                <div className="p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <MapPin className="h-4 w-4 text-green-500" />
                    <span className="text-xs font-medium">Locations</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {data.entities.locations.length > 0 ? (
                      data.entities.locations.map((loc, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {loc}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground">None detected</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Keywords */}
            {data.keywords.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4" />
                  <h4 className="text-sm font-medium">Keywords</h4>
                </div>
                <div className="flex flex-wrap gap-1">
                  {data.keywords.map((keyword, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default EventDetectionPanel;
