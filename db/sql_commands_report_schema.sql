-- ============================================================================
-- AI Summary Feature: Report Schema
-- ============================================================================
-- This script creates the report schema with pool_summaries and final_reports tables
-- Execute these commands directly in your PostgreSQL database

-- Create report schema
CREATE SCHEMA IF NOT EXISTS report;

-- ============================================================================
-- Pool Summaries Table
-- ============================================================================
CREATE TABLE report.pool_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES clinical.children(id) ON DELETE CASCADE,
    pool_id UUID NOT NULL,
    pool_title VARCHAR(255) NOT NULL,
    summary_content JSONB NOT NULL,
    total_sections INTEGER NOT NULL DEFAULT 0,
    completed_sections INTEGER NOT NULL DEFAULT 0,
    total_score INTEGER,
    max_possible_score INTEGER,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_child_pool_summary UNIQUE (child_id, pool_id)
);

-- Add comments for pool_summaries
COMMENT ON TABLE report.pool_summaries IS 'AI-generated summaries for completed assessment pools';
COMMENT ON COLUMN report.pool_summaries.pool_id IS 'Reference to assessment.pools.id (soft reference, no FK constraint)';
COMMENT ON COLUMN report.pool_summaries.pool_title IS 'Denormalized pool title for convenience';
COMMENT ON COLUMN report.pool_summaries.summary_content IS 'AI-generated summary content';
COMMENT ON COLUMN report.pool_summaries.total_sections IS 'Count of sections in this pool';
COMMENT ON COLUMN report.pool_summaries.completed_sections IS 'Count of completed sections';
COMMENT ON COLUMN report.pool_summaries.total_score IS 'Aggregate score across all sections in pool';
COMMENT ON COLUMN report.pool_summaries.max_possible_score IS 'Maximum possible aggregate score';
COMMENT ON COLUMN report.pool_summaries.generated_at IS 'Timestamp when summary was generated';

-- Create indexes for pool_summaries
CREATE INDEX idx_pool_summaries_child ON report.pool_summaries(child_id);
CREATE INDEX idx_pool_summaries_pool ON report.pool_summaries(pool_id);
CREATE INDEX idx_pool_summaries_generated ON report.pool_summaries(generated_at);

-- ============================================================================
-- Final Reports Table
-- ============================================================================
CREATE TABLE report.final_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL UNIQUE REFERENCES clinical.children(id) ON DELETE CASCADE,
    overall_summary JSONB NOT NULL,
    total_pools INTEGER NOT NULL DEFAULT 0,
    completed_pools INTEGER NOT NULL DEFAULT 0,
    overall_score INTEGER,
    overall_max_score INTEGER,
    doctor_reviewed_at TIMESTAMP NULL,
    hod_reviewed_at TIMESTAMP NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Add comments for final_reports
COMMENT ON TABLE report.final_reports IS 'Comprehensive AI-generated final reports combining all pool summaries with two-stage review workflow';
COMMENT ON COLUMN report.final_reports.overall_summary IS 'Comprehensive AI-generated summary including key findings and recommendations';
COMMENT ON COLUMN report.final_reports.total_pools IS 'Total count of pools';
COMMENT ON COLUMN report.final_reports.completed_pools IS 'Count of completed pools with summaries';
COMMENT ON COLUMN report.final_reports.overall_score IS 'Combined score across all pools';
COMMENT ON COLUMN report.final_reports.overall_max_score IS 'Combined maximum possible score';
COMMENT ON COLUMN report.final_reports.doctor_reviewed_at IS 'Timestamp when doctor reviewed/signed the report';
COMMENT ON COLUMN report.final_reports.hod_reviewed_at IS 'Timestamp when HOD reviewed/signed the report (final sign-off)';
COMMENT ON COLUMN report.final_reports.generated_at IS 'Timestamp when report was generated';

-- Create indexes for final_reports
CREATE INDEX idx_final_reports_child ON report.final_reports(child_id);
CREATE INDEX idx_final_reports_generated ON report.final_reports(generated_at);
CREATE INDEX idx_final_reports_doctor_reviewed ON report.final_reports(doctor_reviewed_at);
CREATE INDEX idx_final_reports_hod_reviewed ON report.final_reports(hod_reviewed_at);

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Run these to verify the schema was created successfully

-- Check schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'report';

-- Check tables exist
SELECT table_name FROM information_schema.tables WHERE table_schema = 'report';

-- Check pool_summaries structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'report' AND table_name = 'pool_summaries'
ORDER BY ordinal_position;

-- Check final_reports structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'report' AND table_name = 'final_reports'
ORDER BY ordinal_position;

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'report'
ORDER BY tablename, indexname;
