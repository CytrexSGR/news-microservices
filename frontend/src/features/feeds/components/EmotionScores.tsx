/**
 * Emotion Scores Component
 *
 * Displays emotion analysis from sentiment agent with icons and scores.
 * Shows top 3 emotions detected in the article.
 */

import type { EmotionScores as EmotionScoresType } from '../types/analysisV2';
import { cn } from '@/lib/utils';

interface EmotionScoresProps {
  emotions: EmotionScoresType;
  maxDisplay?: number;
  className?: string;
}

const EMOTION_CONFIG = {
  joy: { icon: '😊', color: 'text-yellow-500', label: 'Joy' },
  anger: { icon: '😠', color: 'text-red-500', label: 'Anger' },
  fear: { icon: '😨', color: 'text-purple-500', label: 'Fear' },
  sadness: { icon: '😢', color: 'text-blue-500', label: 'Sadness' },
  surprise: { icon: '😲', color: 'text-orange-500', label: 'Surprise' },
  disgust: { icon: '🤢', color: 'text-green-500', label: 'Disgust' },
  trust: { icon: '🤝', color: 'text-cyan-500', label: 'Trust' },
  anticipation: { icon: '🔮', color: 'text-indigo-500', label: 'Anticipation' },
};

export function EmotionScores({ emotions, maxDisplay = 3, className }: EmotionScoresProps) {
  // Convert emotions object to sorted array
  const emotionEntries = Object.entries(emotions)
    .filter(([_, score]) => score !== undefined && score > 0)
    .map(([emotion, score]) => ({
      emotion: emotion as keyof typeof EMOTION_CONFIG,
      score: score as number,
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, maxDisplay);

  if (emotionEntries.length === 0) {
    return null;
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {emotionEntries.map(({ emotion, score }) => {
        const config = EMOTION_CONFIG[emotion];
        return (
          <div
            key={emotion}
            className="flex items-center gap-1 text-sm"
            title={`${config.label}: ${(score * 100).toFixed(0)}%`}
          >
            <span className={cn('text-lg', config.color)}>{config.icon}</span>
            <span className="text-muted-foreground font-medium">
              {(score * 100).toFixed(0)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
