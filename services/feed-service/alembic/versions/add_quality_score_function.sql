-- Feed Quality Score Calculation Function
-- Calculates a comprehensive quality score (0-100) based on assessment data

CREATE OR REPLACE FUNCTION calculate_feed_quality_score(
    p_credibility_tier VARCHAR,
    p_reputation_score INTEGER,
    p_editorial_standards JSONB,
    p_trust_ratings JSONB,
    p_health_score INTEGER,
    p_consecutive_failures INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_score INTEGER := 0;
    v_credibility_points INTEGER := 0;
    v_editorial_points INTEGER := 0;
    v_trust_points INTEGER := 0;
    v_health_points INTEGER := 0;
    v_fact_check_level TEXT;
    v_corrections_policy TEXT;
    v_source_attribution TEXT;
    v_newsguard_score INTEGER;
    v_allsides_rating TEXT;
    v_mbfc_rating TEXT;
BEGIN
    -- 1. CREDIBILITY FOUNDATION (40 points)
    CASE p_credibility_tier
        WHEN 'tier_1' THEN v_credibility_points := 40;
        WHEN 'tier_2' THEN v_credibility_points := 30;
        WHEN 'tier_3' THEN v_credibility_points := 20;
        ELSE v_credibility_points := 10; -- unassessed
    END CASE;

    -- 2. EDITORIAL QUALITY (25 points)
    IF p_editorial_standards IS NOT NULL THEN
        -- Fact Checking Level (10 points)
        v_fact_check_level := p_editorial_standards->>'fact_checking_level';
        CASE v_fact_check_level
            WHEN 'high' THEN v_editorial_points := v_editorial_points + 10;
            WHEN 'medium' THEN v_editorial_points := v_editorial_points + 7;
            WHEN 'low' THEN v_editorial_points := v_editorial_points + 3;
            ELSE v_editorial_points := v_editorial_points + 0;
        END CASE;

        -- Corrections Policy (8 points)
        v_corrections_policy := p_editorial_standards->>'corrections_policy';
        CASE v_corrections_policy
            WHEN 'transparent' THEN v_editorial_points := v_editorial_points + 8;
            WHEN 'adequate' THEN v_editorial_points := v_editorial_points + 5;
            WHEN 'poor' THEN v_editorial_points := v_editorial_points + 2;
            ELSE v_editorial_points := v_editorial_points + 0;
        END CASE;

        -- Source Attribution (7 points)
        v_source_attribution := p_editorial_standards->>'source_attribution';
        CASE v_source_attribution
            WHEN 'excellent' THEN v_editorial_points := v_editorial_points + 7;
            WHEN 'good' THEN v_editorial_points := v_editorial_points + 5;
            WHEN 'fair' THEN v_editorial_points := v_editorial_points + 3;
            ELSE v_editorial_points := v_editorial_points + 0;
        END CASE;
    END IF;

    -- 3. EXTERNAL TRUST RATINGS (20 points)
    IF p_trust_ratings IS NOT NULL THEN
        -- NewsGuard Score (8 points)
        v_newsguard_score := (p_trust_ratings->>'newsguard_score')::INTEGER;
        IF v_newsguard_score IS NOT NULL THEN
            v_trust_points := v_trust_points + ROUND((v_newsguard_score::DECIMAL / 100) * 8);
        END IF;

        -- AllSides Rating (7 points)
        v_allsides_rating := LOWER(p_trust_ratings->>'allsides_rating');
        CASE v_allsides_rating
            WHEN 'center' THEN v_trust_points := v_trust_points + 7;
            WHEN 'lean left', 'lean right' THEN v_trust_points := v_trust_points + 5;
            WHEN 'left', 'right' THEN v_trust_points := v_trust_points + 3;
            ELSE v_trust_points := v_trust_points + 0;
        END CASE;

        -- Media Bias Fact Check (5 points)
        v_mbfc_rating := LOWER(p_trust_ratings->>'media_bias_fact_check');
        CASE
            WHEN v_mbfc_rating IN ('least biased', 'high') THEN v_trust_points := v_trust_points + 5;
            WHEN v_mbfc_rating IN ('mostly factual', 'mostly-factual') THEN v_trust_points := v_trust_points + 3;
            WHEN v_mbfc_rating = 'mixed' THEN v_trust_points := v_trust_points + 1;
            ELSE v_trust_points := v_trust_points + 0;
        END CASE;
    END IF;

    -- 4. OPERATIONAL HEALTH (15 points)
    IF p_health_score IS NOT NULL THEN
        v_health_points := ROUND((p_health_score::DECIMAL / 100) * 10);
    ELSE
        v_health_points := 10; -- default if not set
    END IF;

    -- Penalty for consecutive failures (max -5)
    IF p_consecutive_failures IS NOT NULL THEN
        v_health_points := v_health_points - LEAST(p_consecutive_failures, 5);
    END IF;

    -- Ensure health points don't go negative
    v_health_points := GREATEST(v_health_points, 0);

    -- TOTAL SCORE
    v_score := v_credibility_points + v_editorial_points + v_trust_points + v_health_points;

    -- Clamp to 0-100 range
    v_score := LEAST(GREATEST(v_score, 0), 100);

    RETURN v_score;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add quality_score column to feeds table
ALTER TABLE feeds ADD COLUMN IF NOT EXISTS quality_score INTEGER;

-- Create trigger to auto-calculate score on update
CREATE OR REPLACE FUNCTION update_feed_quality_score()
RETURNS TRIGGER AS $$
BEGIN
    NEW.quality_score := calculate_feed_quality_score(
        NEW.credibility_tier,
        NEW.reputation_score,
        NEW.editorial_standards,
        NEW.trust_ratings,
        NEW.health_score,
        NEW.consecutive_failures
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_feed_quality_score ON feeds;
CREATE TRIGGER trigger_update_feed_quality_score
    BEFORE INSERT OR UPDATE ON feeds
    FOR EACH ROW
    EXECUTE FUNCTION update_feed_quality_score();

-- Update existing feeds with calculated scores
UPDATE feeds
SET quality_score = calculate_feed_quality_score(
    credibility_tier,
    reputation_score,
    editorial_standards,
    trust_ratings,
    health_score,
    consecutive_failures
)
WHERE credibility_tier IS NOT NULL OR reputation_score IS NOT NULL;

-- Create index for sorting by quality score
CREATE INDEX IF NOT EXISTS idx_feeds_quality_score ON feeds(quality_score DESC);

COMMENT ON FUNCTION calculate_feed_quality_score IS 'Calculates comprehensive feed quality score (0-100) based on credibility, editorial standards, trust ratings, and operational health';
COMMENT ON COLUMN feeds.quality_score IS 'Calculated quality score (0-100): Premium (85-100), Trusted (70-84), Moderate (50-69), Limited (<50)';
