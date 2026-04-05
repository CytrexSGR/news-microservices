/**
 * Integration tests for ArticleV3AnalysisCard component
 *
 * Tests rendering of V3 Analysis data with validation.
 * Ensures component correctly displays tier0, tier1, tier2 data.
 *
 * Related: POSTMORTEMS.md Incident #23 (2025-11-23)
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ArticleV3AnalysisCard } from '../ArticleV3AnalysisCard';
import {
  mockTier0Kept,
  mockTier0Discarded,
  mockTier1,
  mockTier1LowScores,
  mockTier2,
} from '@/test/mockData/v3Analysis';

describe('ArticleV3AnalysisCard', () => {
  describe('Tier 0 (Triage) Display', () => {
    it('should display priority score', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} />);

      // Full view shows "Priority: 8.5/10"
      expect(screen.getByText(/Priority: 8\.5\/10/i)).toBeInTheDocument();
    });

    it('should display category', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} />);

      expect(screen.getByText('CONFLICT')).toBeInTheDocument();
    });

    it('should show "Keep" badge for kept articles', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} />);

      expect(screen.getByText('Keep')).toBeInTheDocument();
    });

    it('should show "Discard" badge for discarded articles', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Discarded} />);

      expect(screen.getByText('Discard')).toBeInTheDocument();
    });

    it('should apply correct color for high priority (>= 8)', () => {
      const { container } = render(<ArticleV3AnalysisCard tier0={mockTier0Kept} />);

      // High priority should have red color classes
      const badge = container.querySelector('.bg-red-100');
      expect(badge).toBeInTheDocument();
    });

    it('should apply correct color for low priority (< 3)', () => {
      const { container } = render(<ArticleV3AnalysisCard tier0={mockTier0Discarded} />);

      // Low priority should have gray color classes
      const badge = container.querySelector('.bg-gray-100');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Tier 1 (Foundation) Display', () => {
    it('should display foundation scores when tier1 present', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} />);

      // Check for "Tier 1: Foundation Extraction" heading
      expect(screen.getByText(/Tier 1: Foundation Extraction/i)).toBeInTheDocument();

      // Check scores are displayed (using nested structure)
      expect(screen.getByText(/Impact:/i)).toBeInTheDocument();
      expect(screen.getByText(/7\.5/)).toBeInTheDocument();

      expect(screen.getByText(/Credibility:/i)).toBeInTheDocument();
      expect(screen.getByText(/8\.2/)).toBeInTheDocument();

      expect(screen.getByText(/Urgency:/i)).toBeInTheDocument();
      expect(screen.getByText(/6\.1/)).toBeInTheDocument();
    });

    it('should not display tier1 section when tier1 is null', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={null} />);

      // Foundation section should not exist
      expect(screen.queryByText(/Tier 1: Foundation Extraction/i)).not.toBeInTheDocument();
    });

    it('should not display tier1 section when tier1 is undefined', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} />);

      expect(screen.queryByText(/Tier 1: Foundation Extraction/i)).not.toBeInTheDocument();
    });

    it('should display entity count when present', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} />);

      // Component shows entity count as badge: "3 entities"
      expect(screen.getByText(/3 entities/i)).toBeInTheDocument();
    });

    it('should display relation count when present', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} />);

      // Component shows relation count as badge: "2 relations"
      expect(screen.getByText(/2 relations/i)).toBeInTheDocument();
    });

    it('should display topic count when present', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} />);

      // Component shows topic count as badge: "2 topics"
      expect(screen.getByText(/2 topics/i)).toBeInTheDocument();
    });

    it('should apply correct color for high scores (>= 7.0)', () => {
      const { container } = render(
        <ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} />
      );

      // High scores should have green color (text-green-600)
      const highScore = container.querySelector('.text-green-600');
      expect(highScore).toBeInTheDocument();
    });

    it('should apply correct color for low scores (< 4.0)', () => {
      const { container } = render(
        <ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1LowScores} />
      );

      // Low scores should have red color (text-red-600)
      const lowScore = container.querySelector('.text-red-600');
      expect(lowScore).toBeInTheDocument();
    });

    it('should access scores via nested structure (tier1.scores.impact_score)', () => {
      // This test verifies the fix from POSTMORTEMS.md Incident #23
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} />);

      // Should display actual scores, not "N/A"
      expect(screen.getByText(/7\.5/)).toBeInTheDocument();
      expect(screen.getByText(/8\.2/)).toBeInTheDocument();
      expect(screen.getByText(/6\.1/)).toBeInTheDocument();
    });
  });

  describe('Tier 2 (Specialists) Display', () => {
    it('should display specialist count when tier2 present', () => {
      render(
        <ArticleV3AnalysisCard
          tier0={mockTier0Kept}
          tier1={mockTier1}
          tier2={mockTier2}
        />
      );

      // Component shows specialist count in Tier 2 section
      expect(screen.getByText(/Tier 2: Specialist Analysis/i)).toBeInTheDocument();
    });

    it('should not display tier2 section when tier2 is null', () => {
      render(
        <ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} tier2={null} />
      );

      expect(screen.queryByText(/Tier 2: Specialist Analysis/i)).not.toBeInTheDocument();
    });
  });

  describe('Compact Mode', () => {
    it('should render compact view when compact=true', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} compact={true} />);

      // Compact view shows "P8.5" format
      expect(screen.getByText(/P8\.5/i)).toBeInTheDocument();

      // Should show category
      expect(screen.getByText('CONFLICT')).toBeInTheDocument();

      // Should NOT have full card headers
      expect(screen.queryByText('V3 Analysis')).not.toBeInTheDocument();
    });

    it('should render full view when compact=false (default)', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} />);

      // Full view should have card header
      expect(screen.getByText('V3 Analysis')).toBeInTheDocument();

      // Should show full priority format
      expect(screen.getByText(/Priority: 8\.5\/10/i)).toBeInTheDocument();
    });

    it('should show entity count in compact mode', () => {
      render(
        <ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} compact={true} />
      );

      // Compact view shows "3 entities" badge
      expect(screen.getByText(/3 entities/i)).toBeInTheDocument();
    });

    it('should show specialist count in compact mode', () => {
      render(
        <ArticleV3AnalysisCard
          tier0={mockTier0Kept}
          tier1={mockTier1}
          tier2={mockTier2}
          compact={true}
        />
      );

      // Compact view shows "6 specialists" badge
      expect(screen.getByText(/6 specialists/i)).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle tier0 with minimal data', () => {
      const minimalTier0 = {
        PriorityScore: 5.0,
        category: 'OTHER' as const,
        keep: true,
        cost_usd: 0.0001,
        tokens_used: 100,
        model: 'gpt-4o-mini',
      };

      render(<ArticleV3AnalysisCard tier0={minimalTier0} />);

      expect(screen.getByText(/Priority: 5\/10/i)).toBeInTheDocument();
      expect(screen.getByText('OTHER')).toBeInTheDocument();
    });

    it('should apply custom className when provided', () => {
      const { container } = render(
        <ArticleV3AnalysisCard tier0={mockTier0Kept} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('should handle all category types', () => {
      const categories = [
        'CONFLICT',
        'FINANCE',
        'POLITICS',
        'HUMANITARIAN',
        'SECURITY',
        'TECHNOLOGY',
        'OTHER',
      ] as const;

      categories.forEach((category) => {
        const tier0 = { ...mockTier0Kept, category };
        const { unmount } = render(<ArticleV3AnalysisCard tier0={tier0} />);

        expect(screen.getByText(category)).toBeInTheDocument();

        unmount();
      });
    });
  });

  describe('Data Structure Validation', () => {
    it('should correctly access nested scores structure', () => {
      // This verifies the fix from POSTMORTEMS.md Incident #23
      // Component must access tier1.scores.impact_score, not tier1.impact_score

      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} />);

      // mockTier1 has scores nested in 'scores' object
      // Component should find them and display correctly
      expect(screen.getByText(/7\.5/)).toBeInTheDocument();
      expect(screen.getByText(/8\.2/)).toBeInTheDocument();
      expect(screen.getByText(/6\.1/)).toBeInTheDocument();
    });

    it('should display total cost across all tiers', () => {
      render(
        <ArticleV3AnalysisCard
          tier0={mockTier0Kept}
          tier1={mockTier1}
          tier2={mockTier2}
        />
      );

      // Cost badge shows sum of all tier costs
      // tier0: 0.00012, tier1: 0.00045, tier2: 0.00095
      // Total: 0.00152
      expect(screen.getByText(/Cost: \$0\.00152/i)).toBeInTheDocument();
    });

    it('should handle tier1 without tier2', () => {
      render(<ArticleV3AnalysisCard tier0={mockTier0Kept} tier1={mockTier1} />);

      // Should still show tier1 data
      expect(screen.getByText(/Tier 1: Foundation Extraction/i)).toBeInTheDocument();

      // But not tier2
      expect(screen.queryByText(/Tier 2: Specialist Analysis/i)).not.toBeInTheDocument();
    });
  });
});
