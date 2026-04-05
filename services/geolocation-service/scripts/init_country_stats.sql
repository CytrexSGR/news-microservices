-- Initialize country_stats for all countries
-- This ensures every country has a stats row for fast updates

INSERT INTO country_stats (country_code, article_count_24h, article_count_7d, article_count_30d)
SELECT iso_code, 0, 0, 0 FROM countries
ON CONFLICT (country_code) DO NOTHING;

-- Show results
SELECT
    'Initialized ' || COUNT(*) || ' country stats rows' as result
FROM country_stats;

-- Verify the data
SELECT
    c.iso_code,
    c.name,
    c.name_de,
    c.region,
    cs.article_count_24h,
    cs.article_count_7d,
    cs.article_count_30d
FROM countries c
LEFT JOIN country_stats cs ON c.iso_code = cs.country_code
ORDER BY c.region, c.name
LIMIT 20;
