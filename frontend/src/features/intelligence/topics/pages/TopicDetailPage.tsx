// frontend/src/features/intelligence/topics/pages/TopicDetailPage.tsx

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Tag,
  Hash,
  FileText,
  ExternalLink,
  Edit2,
  Check,
  X,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/Input';
import { useTopic, useSubmitFeedback } from '../api/useTopics';

export function TopicDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const topicId = Number(id);

  const { data: topic, isLoading, error } = useTopic(topicId, !isNaN(topicId));
  const feedbackMutation = useSubmitFeedback();

  const [isEditing, setIsEditing] = useState(false);
  const [newLabel, setNewLabel] = useState('');

  // Handle label edit
  const startEditing = () => {
    setNewLabel(topic?.label || '');
    setIsEditing(true);
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setNewLabel('');
  };

  const submitLabel = async () => {
    if (!newLabel.trim() || !topic) return;

    try {
      await feedbackMutation.mutateAsync({
        clusterId: topic.id,
        feedback: { label: newLabel.trim(), confidence: 1.0 },
      });
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to update label:', err);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto py-12 text-center">
        <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
        <p className="mt-2 text-muted-foreground">Loading topic...</p>
      </div>
    );
  }

  // Error state
  if (error || !topic) {
    return (
      <div className="container mx-auto py-12">
        <Card className="max-w-md mx-auto">
          <CardContent className="py-12 text-center">
            <AlertTriangle className="h-12 w-12 mx-auto text-destructive" />
            <h3 className="mt-4 text-lg font-medium">Topic Not Found</h3>
            <p className="text-muted-foreground mb-4">
              The requested topic could not be loaded.
            </p>
            <Button onClick={() => navigate('/intelligence/topics')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Topics
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Back Button */}
      <Button variant="ghost" onClick={() => navigate('/intelligence/topics')}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Topics
      </Button>

      {/* Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <Input
                    value={newLabel}
                    onChange={(e) => setNewLabel(e.target.value)}
                    placeholder="Enter topic label..."
                    className="max-w-md"
                    autoFocus
                  />
                  <Button
                    size="sm"
                    onClick={submitLabel}
                    disabled={!newLabel.trim() || feedbackMutation.isPending}
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="outline" onClick={cancelEditing}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Tag className="h-5 w-5 text-muted-foreground" />
                  <CardTitle className="text-xl">
                    {topic.label || `Topic #${topic.id}`}
                  </CardTitle>
                  <Button size="sm" variant="ghost" onClick={startEditing}>
                    <Edit2 className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>
            <Badge variant="secondary" className="text-lg px-3 py-1">
              <Hash className="h-4 w-4 mr-1" />
              {topic.article_count} Articles
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {/* Keywords */}
          {topic.keywords && topic.keywords.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium mb-2">Keywords</h4>
              <div className="flex flex-wrap gap-2">
                {topic.keywords.map((kw, i) => (
                  <Badge key={i} variant="outline">
                    {kw}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Cluster Index:</span>
              <span className="ml-2 font-medium">{topic.cluster_idx}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Batch:</span>
              <span className="ml-2 font-mono text-xs">{topic.batch_id.slice(0, 8)}...</span>
            </div>
            {topic.label_confidence && (
              <div>
                <span className="text-muted-foreground">Confidence:</span>
                <span className="ml-2 font-medium">
                  {(topic.label_confidence * 100).toFixed(0)}%
                </span>
              </div>
            )}
            {topic.created_at && (
              <div>
                <span className="text-muted-foreground">Created:</span>
                <span className="ml-2">{new Date(topic.created_at).toLocaleDateString()}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Sample Articles */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Sample Articles ({topic.sample_articles.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {topic.sample_articles.length > 0 ? (
            <div className="space-y-3">
              {topic.sample_articles.map((article, index) => (
                <div
                  key={article.article_id}
                  className="flex items-start justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground font-mono">
                        #{index + 1}
                      </span>
                      <h4 className="font-medium truncate">{article.title}</h4>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                      {article.distance !== undefined && (
                        <span>Distance: {article.distance.toFixed(3)}</span>
                      )}
                      {article.published_at && (
                        <span>Published: {new Date(article.published_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0 ml-2"
                    >
                      <Button size="sm" variant="ghost">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </a>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No sample articles available
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default TopicDetailPage;
