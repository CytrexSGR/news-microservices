/**
 * Zod validation schema for Feed Creation
 */
import { z } from 'zod';
import { FEED_CATEGORIES } from '../types/createFeed';

export const createFeedSchema = z.object({
  // Basic Info
  name: z
    .string()
    .min(1, 'Name ist erforderlich')
    .max(200, 'Name darf maximal 200 Zeichen lang sein'),

  url: z
    .string()
    .url('Ungültige URL. Bitte eine gültige HTTP/HTTPS URL eingeben')
    .refine((url) => url.startsWith('http://') || url.startsWith('https://'), {
      message: 'URL muss mit http:// oder https:// beginnen',
    }),

  description: z.string().optional(),

  category: z.enum(FEED_CATEGORIES as unknown as [string, ...string[]]).optional(),

  fetch_interval: z
    .number()
    .int()
    .min(5, 'Fetch-Intervall muss mindestens 5 Minuten betragen')
    .max(1440, 'Fetch-Intervall darf maximal 1440 Minuten (24 Stunden) betragen'),

  // Scraping Configuration
  scrape_full_content: z.boolean(),

  scrape_method: z.enum(['newspaper4k', 'playwright']),

  scrape_failure_threshold: z
    .number()
    .int()
    .min(1, 'Threshold muss mindestens 1 sein')
    .max(20, 'Threshold darf maximal 20 sein'),

  // Auto-Analysis Configuration
  enable_categorization: z.boolean(),
  enable_finance_sentiment: z.boolean(),
  enable_geopolitical_sentiment: z.boolean(),
  enable_osint_analysis: z.boolean(),
  enable_summary: z.boolean(),
  enable_entity_extraction: z.boolean(),
  enable_topic_classification: z.boolean(),

  // Source Assessment (optional) - all fields can be undefined or null
  // Using z.any() to be maximally permissive for these optional nested objects
  credibility_tier: z.string().optional().nullable(),
  reputation_score: z.number().int().min(0).max(100).optional().nullable(),
  founded_year: z.number().int().optional().nullable(),
  organization_type: z.string().optional().nullable(),
  political_bias: z.string().optional().nullable(),
  editorial_standards: z.any().optional(),
  trust_ratings: z.any().optional(),
  recommendation: z.any().optional(),
  assessment_summary: z.string().optional().nullable(),
});

export type CreateFeedSchemaType = z.infer<typeof createFeedSchema>;
