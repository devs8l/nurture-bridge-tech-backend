-- Migration: Add name column to users, doctors, and parents tables
-- Date: 2025-12-19

BEGIN;

-- Add name column to auth.users table
ALTER TABLE auth.users 
ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT 'NBT_super_admin';

-- Add name column to clinical.doctors table
ALTER TABLE clinical.doctors 
ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT 'Doctor';

-- Add name column to clinical.parents table
ALTER TABLE clinical.parents 
ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT 'Parent';

COMMIT;
