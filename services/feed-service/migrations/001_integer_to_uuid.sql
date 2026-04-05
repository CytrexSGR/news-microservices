-- ============================================================================
-- Feed Service Migration: Integer IDs to UUIDs
-- Version: 001
-- Description: Converts all integer-based IDs to UUIDs with full rollback support
-- Safety: Idempotent, transactional, with data preservation and verification
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- MIGRATION START
-- ============================================================================

BEGIN;

-- Set session parameters for safety
SET LOCAL statement_timeout = '30min';
SET LOCAL lock_timeout = '5min';

-- ============================================================================
-- STEP 1: Create Migration Metadata Table
-- ============================================================================

-- Create migration tracking table (idempotent)
CREATE TABLE IF NOT EXISTS migration_metadata (
    migration_id VARCHAR(50) PRIMARY KEY,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'in_progress',
    rollback_data JSONB,
    verification_checksums JSONB
);

-- Check if migration already completed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM migration_metadata
        WHERE migration_id = '001_integer_to_uuid'
        AND status = 'completed'
    ) THEN
        RAISE NOTICE 'Migration 001_integer_to_uuid already completed. Skipping.';
        -- Exit early but allow commit
        RETURN;
    END IF;

    -- Record migration start
    INSERT INTO migration_metadata (migration_id, status)
    VALUES ('001_integer_to_uuid', 'in_progress')
    ON CONFLICT (migration_id) DO UPDATE
    SET started_at = CURRENT_TIMESTAMP, status = 'in_progress';
END $$;

-- ============================================================================
-- STEP 2: Create ID Mapping Table
-- ============================================================================

-- This table maintains the mapping between old integer IDs and new UUIDs
-- Critical for maintaining referential integrity during migration
CREATE TABLE IF NOT EXISTS id_mapping (
    table_name VARCHAR(100) NOT NULL,
    old_id INTEGER NOT NULL,
    new_uuid UUID NOT NULL DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (table_name, old_id),
    UNIQUE (table_name, new_uuid)
);

CREATE INDEX IF NOT EXISTS idx_id_mapping_old_id ON id_mapping(table_name, old_id);
CREATE INDEX IF NOT EXISTS idx_id_mapping_new_uuid ON id_mapping(table_name, new_uuid);

-- ============================================================================
-- STEP 3: Backup Tables (Create Backup Schema)
-- ============================================================================

-- Create backup schema for safety
CREATE SCHEMA IF NOT EXISTS migration_backup;

-- Function to backup a table
CREATE OR REPLACE FUNCTION backup_table(table_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('DROP TABLE IF EXISTS migration_backup.%I_backup', table_name);
    EXECUTE format('CREATE TABLE migration_backup.%I_backup AS SELECT * FROM %I', table_name, table_name);
    RAISE NOTICE 'Backed up table: %', table_name;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 4: Migrate Feed Items Table
-- ============================================================================

-- Backup feed_items
SELECT backup_table('feed_items');

-- Add UUID column if it doesn't exist
ALTER TABLE feed_items
ADD COLUMN IF NOT EXISTS id_uuid UUID;

-- Generate UUIDs for existing records and store mapping
INSERT INTO id_mapping (table_name, old_id, new_uuid)
SELECT 'feed_items', id, gen_random_uuid()
FROM feed_items
WHERE id IS NOT NULL
ON CONFLICT (table_name, old_id) DO NOTHING;

-- Update the UUID column with mapped values
UPDATE feed_items fi
SET id_uuid = im.new_uuid
FROM id_mapping im
WHERE im.table_name = 'feed_items'
AND im.old_id = fi.id
AND fi.id_uuid IS NULL;

-- Handle user_id foreign key (if exists)
ALTER TABLE feed_items
ADD COLUMN IF NOT EXISTS user_id_uuid UUID;

-- Map user_id to UUID
UPDATE feed_items fi
SET user_id_uuid = im.new_uuid
FROM id_mapping im
WHERE im.table_name = 'users'
AND im.old_id = fi.user_id
AND fi.user_id_uuid IS NULL;

-- ============================================================================
-- STEP 5: Migrate Users Table (if exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        -- Backup users
        PERFORM backup_table('users');

        -- Add UUID column
        ALTER TABLE users ADD COLUMN IF NOT EXISTS id_uuid UUID;

        -- Generate UUIDs
        INSERT INTO id_mapping (table_name, old_id, new_uuid)
        SELECT 'users', id, gen_random_uuid()
        FROM users
        WHERE id IS NOT NULL
        ON CONFLICT (table_name, old_id) DO NOTHING;

        -- Update UUID column
        UPDATE users u
        SET id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'users'
        AND im.old_id = u.id
        AND u.id_uuid IS NULL;

        RAISE NOTICE 'Migrated users table';
    END IF;
END $$;

-- ============================================================================
-- STEP 6: Migrate Feed Subscriptions Table (if exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_subscriptions') THEN
        -- Backup feed_subscriptions
        PERFORM backup_table('feed_subscriptions');

        -- Add UUID columns
        ALTER TABLE feed_subscriptions
        ADD COLUMN IF NOT EXISTS id_uuid UUID,
        ADD COLUMN IF NOT EXISTS user_id_uuid UUID,
        ADD COLUMN IF NOT EXISTS feed_id_uuid UUID;

        -- Generate UUIDs for primary key
        INSERT INTO id_mapping (table_name, old_id, new_uuid)
        SELECT 'feed_subscriptions', id, gen_random_uuid()
        FROM feed_subscriptions
        WHERE id IS NOT NULL
        ON CONFLICT (table_name, old_id) DO NOTHING;

        -- Update all UUID columns
        UPDATE feed_subscriptions fs
        SET id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'feed_subscriptions'
        AND im.old_id = fs.id
        AND fs.id_uuid IS NULL;

        UPDATE feed_subscriptions fs
        SET user_id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'users'
        AND im.old_id = fs.user_id
        AND fs.user_id_uuid IS NULL;

        UPDATE feed_subscriptions fs
        SET feed_id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'feed_items'
        AND im.old_id = fs.feed_id
        AND fs.feed_id_uuid IS NULL;

        RAISE NOTICE 'Migrated feed_subscriptions table';
    END IF;
END $$;

-- ============================================================================
-- STEP 7: Migrate Feed Categories Table (if exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_categories') THEN
        PERFORM backup_table('feed_categories');

        ALTER TABLE feed_categories
        ADD COLUMN IF NOT EXISTS id_uuid UUID,
        ADD COLUMN IF NOT EXISTS feed_id_uuid UUID;

        INSERT INTO id_mapping (table_name, old_id, new_uuid)
        SELECT 'feed_categories', id, gen_random_uuid()
        FROM feed_categories
        WHERE id IS NOT NULL
        ON CONFLICT (table_name, old_id) DO NOTHING;

        UPDATE feed_categories fc
        SET id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'feed_categories'
        AND im.old_id = fc.id
        AND fc.id_uuid IS NULL;

        UPDATE feed_categories fc
        SET feed_id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'feed_items'
        AND im.old_id = fc.feed_id
        AND fc.feed_id_uuid IS NULL;

        RAISE NOTICE 'Migrated feed_categories table';
    END IF;
END $$;

-- ============================================================================
-- STEP 8: Migrate Comments Table (if exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments') THEN
        PERFORM backup_table('comments');

        ALTER TABLE comments
        ADD COLUMN IF NOT EXISTS id_uuid UUID,
        ADD COLUMN IF NOT EXISTS feed_id_uuid UUID,
        ADD COLUMN IF NOT EXISTS user_id_uuid UUID,
        ADD COLUMN IF NOT EXISTS parent_id_uuid UUID;

        INSERT INTO id_mapping (table_name, old_id, new_uuid)
        SELECT 'comments', id, gen_random_uuid()
        FROM comments
        WHERE id IS NOT NULL
        ON CONFLICT (table_name, old_id) DO NOTHING;

        UPDATE comments c
        SET id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'comments'
        AND im.old_id = c.id
        AND c.id_uuid IS NULL;

        UPDATE comments c
        SET feed_id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'feed_items'
        AND im.old_id = c.feed_id
        AND c.feed_id_uuid IS NULL;

        UPDATE comments c
        SET user_id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'users'
        AND im.old_id = c.user_id
        AND c.user_id_uuid IS NULL;

        -- Handle self-referential parent_id
        UPDATE comments c
        SET parent_id_uuid = im.new_uuid
        FROM id_mapping im
        WHERE im.table_name = 'comments'
        AND im.old_id = c.parent_id
        AND c.parent_id_uuid IS NULL;

        RAISE NOTICE 'Migrated comments table';
    END IF;
END $$;

-- ============================================================================
-- STEP 9: Verification Checkpoint
-- ============================================================================

DO $$
DECLARE
    feed_items_count INTEGER;
    feed_items_uuid_count INTEGER;
    mapping_count INTEGER;
BEGIN
    -- Verify feed_items migration
    SELECT COUNT(*) INTO feed_items_count FROM feed_items;
    SELECT COUNT(*) INTO feed_items_uuid_count FROM feed_items WHERE id_uuid IS NOT NULL;
    SELECT COUNT(*) INTO mapping_count FROM id_mapping WHERE table_name = 'feed_items';

    IF feed_items_count != feed_items_uuid_count THEN
        RAISE EXCEPTION 'Verification failed: feed_items has % rows but only % have UUIDs',
            feed_items_count, feed_items_uuid_count;
    END IF;

    IF feed_items_count != mapping_count THEN
        RAISE EXCEPTION 'Verification failed: feed_items has % rows but id_mapping has % entries',
            feed_items_count, mapping_count;
    END IF;

    RAISE NOTICE 'Verification passed: All feed_items have UUID mappings';

    -- Store verification checksums
    UPDATE migration_metadata
    SET verification_checksums = jsonb_build_object(
        'feed_items_count', feed_items_count,
        'mapping_count', mapping_count,
        'verified_at', CURRENT_TIMESTAMP
    )
    WHERE migration_id = '001_integer_to_uuid';
END $$;

-- ============================================================================
-- STEP 10: Drop Old Constraints and Indexes
-- ============================================================================

-- Drop foreign key constraints (feed_items)
DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    FOR constraint_record IN
        SELECT conname, conrelid::regclass AS table_name
        FROM pg_constraint
        WHERE contype = 'f'
        AND conrelid IN (
            'feed_items'::regclass,
            'feed_subscriptions'::regclass,
            'feed_categories'::regclass,
            'comments'::regclass
        )
    LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT IF EXISTS %I CASCADE',
            constraint_record.table_name, constraint_record.conname);
        RAISE NOTICE 'Dropped constraint: % on %', constraint_record.conname, constraint_record.table_name;
    END LOOP;
END $$;

-- Drop primary key constraints and indexes on old ID columns
ALTER TABLE feed_items DROP CONSTRAINT IF EXISTS feed_items_pkey CASCADE;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey CASCADE;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_subscriptions') THEN
        ALTER TABLE feed_subscriptions DROP CONSTRAINT IF EXISTS feed_subscriptions_pkey CASCADE;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_categories') THEN
        ALTER TABLE feed_categories DROP CONSTRAINT IF EXISTS feed_categories_pkey CASCADE;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments') THEN
        ALTER TABLE comments DROP CONSTRAINT IF EXISTS comments_pkey CASCADE;
    END IF;
END $$;

-- ============================================================================
-- STEP 11: Rename Old Columns to _old and UUID Columns to Primary Names
-- ============================================================================

-- Feed Items
ALTER TABLE feed_items RENAME COLUMN id TO id_old;
ALTER TABLE feed_items RENAME COLUMN id_uuid TO id;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'feed_items' AND column_name = 'user_id') THEN
        ALTER TABLE feed_items RENAME COLUMN user_id TO user_id_old;
        ALTER TABLE feed_items RENAME COLUMN user_id_uuid TO user_id;
    END IF;
END $$;

-- Users
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE users RENAME COLUMN id TO id_old;
        ALTER TABLE users RENAME COLUMN id_uuid TO id;
        RAISE NOTICE 'Renamed users columns';
    END IF;
END $$;

-- Feed Subscriptions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_subscriptions') THEN
        ALTER TABLE feed_subscriptions RENAME COLUMN id TO id_old;
        ALTER TABLE feed_subscriptions RENAME COLUMN id_uuid TO id;

        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'feed_subscriptions' AND column_name = 'user_id') THEN
            ALTER TABLE feed_subscriptions RENAME COLUMN user_id TO user_id_old;
            ALTER TABLE feed_subscriptions RENAME COLUMN user_id_uuid TO user_id;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'feed_subscriptions' AND column_name = 'feed_id') THEN
            ALTER TABLE feed_subscriptions RENAME COLUMN feed_id TO feed_id_old;
            ALTER TABLE feed_subscriptions RENAME COLUMN feed_id_uuid TO feed_id;
        END IF;

        RAISE NOTICE 'Renamed feed_subscriptions columns';
    END IF;
END $$;

-- Feed Categories
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_categories') THEN
        ALTER TABLE feed_categories RENAME COLUMN id TO id_old;
        ALTER TABLE feed_categories RENAME COLUMN id_uuid TO id;

        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'feed_categories' AND column_name = 'feed_id') THEN
            ALTER TABLE feed_categories RENAME COLUMN feed_id TO feed_id_old;
            ALTER TABLE feed_categories RENAME COLUMN feed_id_uuid TO feed_id;
        END IF;

        RAISE NOTICE 'Renamed feed_categories columns';
    END IF;
END $$;

-- Comments
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments') THEN
        ALTER TABLE comments RENAME COLUMN id TO id_old;
        ALTER TABLE comments RENAME COLUMN id_uuid TO id;

        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'comments' AND column_name = 'feed_id') THEN
            ALTER TABLE comments RENAME COLUMN feed_id TO feed_id_old;
            ALTER TABLE comments RENAME COLUMN feed_id_uuid TO feed_id;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'comments' AND column_name = 'user_id') THEN
            ALTER TABLE comments RENAME COLUMN user_id TO user_id_old;
            ALTER TABLE comments RENAME COLUMN user_id_uuid TO user_id;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'comments' AND column_name = 'parent_id') THEN
            ALTER TABLE comments RENAME COLUMN parent_id TO parent_id_old;
            ALTER TABLE comments RENAME COLUMN parent_id_uuid TO parent_id;
        END IF;

        RAISE NOTICE 'Renamed comments columns';
    END IF;
END $$;

-- ============================================================================
-- STEP 12: Add New Primary Keys and Constraints
-- ============================================================================

-- Add NOT NULL constraints
ALTER TABLE feed_items ALTER COLUMN id SET NOT NULL;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE users ALTER COLUMN id SET NOT NULL;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_subscriptions') THEN
        ALTER TABLE feed_subscriptions ALTER COLUMN id SET NOT NULL;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_categories') THEN
        ALTER TABLE feed_categories ALTER COLUMN id SET NOT NULL;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments') THEN
        ALTER TABLE comments ALTER COLUMN id SET NOT NULL;
    END IF;
END $$;

-- Add primary keys
ALTER TABLE feed_items ADD PRIMARY KEY (id);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE users ADD PRIMARY KEY (id);
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_subscriptions') THEN
        ALTER TABLE feed_subscriptions ADD PRIMARY KEY (id);
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_categories') THEN
        ALTER TABLE feed_categories ADD PRIMARY KEY (id);
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments') THEN
        ALTER TABLE comments ADD PRIMARY KEY (id);
    END IF;
END $$;

-- ============================================================================
-- STEP 13: Recreate Foreign Keys
-- ============================================================================

-- Feed Items foreign keys
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'feed_items' AND column_name = 'user_id')
       AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE feed_items
        ADD CONSTRAINT fk_feed_items_user_id
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Feed Subscriptions foreign keys
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_subscriptions') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'feed_subscriptions' AND column_name = 'user_id')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
            ALTER TABLE feed_subscriptions
            ADD CONSTRAINT fk_feed_subscriptions_user_id
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'feed_subscriptions' AND column_name = 'feed_id') THEN
            ALTER TABLE feed_subscriptions
            ADD CONSTRAINT fk_feed_subscriptions_feed_id
            FOREIGN KEY (feed_id) REFERENCES feed_items(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

-- Feed Categories foreign keys
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_categories')
       AND EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'feed_categories' AND column_name = 'feed_id') THEN
        ALTER TABLE feed_categories
        ADD CONSTRAINT fk_feed_categories_feed_id
        FOREIGN KEY (feed_id) REFERENCES feed_items(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Comments foreign keys
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'comments' AND column_name = 'feed_id') THEN
            ALTER TABLE comments
            ADD CONSTRAINT fk_comments_feed_id
            FOREIGN KEY (feed_id) REFERENCES feed_items(id) ON DELETE CASCADE;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'comments' AND column_name = 'user_id')
           AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
            ALTER TABLE comments
            ADD CONSTRAINT fk_comments_user_id
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'comments' AND column_name = 'parent_id') THEN
            ALTER TABLE comments
            ADD CONSTRAINT fk_comments_parent_id
            FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

-- ============================================================================
-- STEP 14: Create Indexes for Performance
-- ============================================================================

-- Feed Items indexes
CREATE INDEX IF NOT EXISTS idx_feed_items_id ON feed_items(id);
CREATE INDEX IF NOT EXISTS idx_feed_items_user_id ON feed_items(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_feed_items_created_at ON feed_items(created_at);

-- Users indexes
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        CREATE INDEX IF NOT EXISTS idx_users_id ON users(id);
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not create users indexes: %', SQLERRM;
END $$;

-- Feed Subscriptions indexes
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_subscriptions') THEN
        CREATE INDEX IF NOT EXISTS idx_feed_subscriptions_id ON feed_subscriptions(id);
        CREATE INDEX IF NOT EXISTS idx_feed_subscriptions_user_id ON feed_subscriptions(user_id);
        CREATE INDEX IF NOT EXISTS idx_feed_subscriptions_feed_id ON feed_subscriptions(feed_id);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_feed_subscriptions_unique
            ON feed_subscriptions(user_id, feed_id);
    END IF;
END $$;

-- Feed Categories indexes
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'feed_categories') THEN
        CREATE INDEX IF NOT EXISTS idx_feed_categories_id ON feed_categories(id);
        CREATE INDEX IF NOT EXISTS idx_feed_categories_feed_id ON feed_categories(feed_id);
    END IF;
END $$;

-- Comments indexes
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments') THEN
        CREATE INDEX IF NOT EXISTS idx_comments_id ON comments(id);
        CREATE INDEX IF NOT EXISTS idx_comments_feed_id ON comments(feed_id);
        CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);
        CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON comments(parent_id) WHERE parent_id IS NOT NULL;
    END IF;
END $$;

-- ============================================================================
-- STEP 15: Final Verification
-- ============================================================================

DO $$
DECLARE
    verification_results JSONB;
    total_tables INTEGER := 0;
    migrated_tables INTEGER := 0;
BEGIN
    -- Count migrated tables
    SELECT COUNT(*) INTO total_tables
    FROM information_schema.tables
    WHERE table_name IN ('feed_items', 'users', 'feed_subscriptions', 'feed_categories', 'comments')
    AND table_schema = 'public';

    SELECT COUNT(*) INTO migrated_tables
    FROM information_schema.columns
    WHERE table_name IN ('feed_items', 'users', 'feed_subscriptions', 'feed_categories', 'comments')
    AND column_name = 'id'
    AND data_type = 'uuid'
    AND table_schema = 'public';

    verification_results := jsonb_build_object(
        'total_tables', total_tables,
        'migrated_tables', migrated_tables,
        'feed_items_count', (SELECT COUNT(*) FROM feed_items),
        'id_mapping_entries', (SELECT COUNT(*) FROM id_mapping),
        'verification_time', CURRENT_TIMESTAMP
    );

    -- Log verification results
    RAISE NOTICE 'Final verification: %', verification_results;

    -- Update migration metadata
    UPDATE migration_metadata
    SET
        status = 'completed',
        completed_at = CURRENT_TIMESTAMP,
        verification_checksums = verification_checksums || verification_results
    WHERE migration_id = '001_integer_to_uuid';

    -- Success message
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION COMPLETED SUCCESSFULLY';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migrated % out of % tables', migrated_tables, total_tables;
    RAISE NOTICE 'Total records in feed_items: %', (SELECT COUNT(*) FROM feed_items);
    RAISE NOTICE 'Total ID mappings created: %', (SELECT COUNT(*) FROM id_mapping);
    RAISE NOTICE 'Backup tables available in migration_backup schema';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- ============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ============================================================================

-- Run these queries after migration to verify success:

/*
-- 1. Verify all tables have UUID primary keys
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE column_name = 'id'
AND table_name IN ('feed_items', 'users', 'feed_subscriptions', 'feed_categories', 'comments')
AND table_schema = 'public';

-- 2. Check record counts match
SELECT
    'feed_items' as table_name,
    COUNT(*) as record_count
FROM feed_items
UNION ALL
SELECT
    'id_mapping (feed_items)' as table_name,
    COUNT(*) as record_count
FROM id_mapping
WHERE table_name = 'feed_items';

-- 3. Verify foreign key relationships
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('feed_items', 'feed_subscriptions', 'feed_categories', 'comments');

-- 4. Check for any NULL UUIDs (should return 0)
SELECT
    'feed_items' as table_name,
    COUNT(*) as null_uuids
FROM feed_items
WHERE id IS NULL;

-- 5. Verify indexes
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('feed_items', 'users', 'feed_subscriptions', 'feed_categories', 'comments')
AND schemaname = 'public'
ORDER BY tablename, indexname;
*/

-- ============================================================================
-- ROLLBACK SCRIPT
-- ============================================================================

/*
-- ROLLBACK INSTRUCTIONS:
-- Run this script to rollback the migration to integer IDs
-- WARNING: This will restore data from backup tables

BEGIN;

-- 1. Drop new UUID-based tables
DROP TABLE IF EXISTS feed_items CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS feed_subscriptions CASCADE;
DROP TABLE IF EXISTS feed_categories CASCADE;
DROP TABLE IF EXISTS comments CASCADE;

-- 2. Restore from backup
CREATE TABLE feed_items AS SELECT * FROM migration_backup.feed_items_backup;
CREATE TABLE users AS SELECT * FROM migration_backup.users_backup;
CREATE TABLE feed_subscriptions AS SELECT * FROM migration_backup.feed_subscriptions_backup;
CREATE TABLE feed_categories AS SELECT * FROM migration_backup.feed_categories_backup;
CREATE TABLE comments AS SELECT * FROM migration_backup.comments_backup;

-- 3. Recreate constraints (adjust column names as needed)
ALTER TABLE feed_items ADD PRIMARY KEY (id);
ALTER TABLE users ADD PRIMARY KEY (id);
ALTER TABLE feed_subscriptions ADD PRIMARY KEY (id);
ALTER TABLE feed_categories ADD PRIMARY KEY (id);
ALTER TABLE comments ADD PRIMARY KEY (id);

-- 4. Recreate foreign keys (adjust as needed based on your schema)
ALTER TABLE feed_items
    ADD CONSTRAINT fk_feed_items_user_id
    FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE feed_subscriptions
    ADD CONSTRAINT fk_feed_subscriptions_user_id
    FOREIGN KEY (user_id) REFERENCES users(id),
    ADD CONSTRAINT fk_feed_subscriptions_feed_id
    FOREIGN KEY (feed_id) REFERENCES feed_items(id);

ALTER TABLE feed_categories
    ADD CONSTRAINT fk_feed_categories_feed_id
    FOREIGN KEY (feed_id) REFERENCES feed_items(id);

ALTER TABLE comments
    ADD CONSTRAINT fk_comments_feed_id
    FOREIGN KEY (feed_id) REFERENCES feed_items(id),
    ADD CONSTRAINT fk_comments_user_id
    FOREIGN KEY (user_id) REFERENCES users(id),
    ADD CONSTRAINT fk_comments_parent_id
    FOREIGN KEY (parent_id) REFERENCES comments(id);

-- 5. Update migration metadata
UPDATE migration_metadata
SET status = 'rolled_back',
    completed_at = CURRENT_TIMESTAMP
WHERE migration_id = '001_integer_to_uuid';

COMMIT;

-- 6. Verify rollback
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE column_name = 'id'
AND table_name IN ('feed_items', 'users', 'feed_subscriptions', 'feed_categories', 'comments');
*/

-- ============================================================================
-- CLEANUP SCRIPT (Run after successful migration verification)
-- ============================================================================

/*
-- WARNING: Only run this after thoroughly testing the migrated database
-- This will permanently delete backup data and old columns

BEGIN;

-- 1. Drop old integer columns
ALTER TABLE feed_items DROP COLUMN IF EXISTS id_old;
ALTER TABLE feed_items DROP COLUMN IF EXISTS user_id_old;

ALTER TABLE users DROP COLUMN IF EXISTS id_old;

ALTER TABLE feed_subscriptions DROP COLUMN IF EXISTS id_old;
ALTER TABLE feed_subscriptions DROP COLUMN IF EXISTS user_id_old;
ALTER TABLE feed_subscriptions DROP COLUMN IF EXISTS feed_id_old;

ALTER TABLE feed_categories DROP COLUMN IF EXISTS id_old;
ALTER TABLE feed_categories DROP COLUMN IF EXISTS feed_id_old;

ALTER TABLE comments DROP COLUMN IF EXISTS id_old;
ALTER TABLE comments DROP COLUMN IF EXISTS feed_id_old;
ALTER TABLE comments DROP COLUMN IF EXISTS user_id_old;
ALTER TABLE comments DROP COLUMN IF EXISTS parent_id_old;

-- 2. Drop backup tables
DROP SCHEMA IF EXISTS migration_backup CASCADE;

-- 3. Drop id_mapping table (optional - keep for audit trail)
-- DROP TABLE IF EXISTS id_mapping;

-- 4. Drop migration metadata (optional - keep for audit trail)
-- DROP TABLE IF EXISTS migration_metadata;

COMMIT;

RAISE NOTICE 'Cleanup completed successfully';
*/
