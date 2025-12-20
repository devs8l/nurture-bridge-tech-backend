-- Migration: Add HOD, Receptionist roles and department field
-- Date: 2025-12-19
-- Description: Adds HOD and RECEPTIONIST roles, creates new staff tables, refactors Doctor model

-- Step 1: Add new roles to UserRole enum
ALTER TYPE auth.user_role ADD VALUE IF NOT EXISTS 'HOD';
ALTER TYPE auth.user_role ADD VALUE IF NOT EXISTS 'RECEPTIONIST';

-- Step 2: Create HOD table
CREATE TABLE IF NOT EXISTS clinical.hods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id),
    tenant_id UUID NOT NULL REFERENCES tenant.tenants(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    department VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);

COMMENT ON TABLE clinical.hods IS 'Head of Department - Clinical authority';
COMMENT ON COLUMN clinical.hods.user_id IS '1-to-1 link with auth.users (enforced even with soft-delete)';
COMMENT ON COLUMN clinical.hods.department IS 'Organizational department (e.g., Pediatrics, Neurology)';

CREATE INDEX idx_hods_user_id ON clinical.hods(user_id);
CREATE INDEX idx_hods_tenant_id ON clinical.hods(tenant_id);
CREATE INDEX idx_hods_department ON clinical.hods(department);

-- Step 3: Create Receptionist table
CREATE TABLE IF NOT EXISTS clinical.receptionists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id),
    tenant_id UUID NOT NULL REFERENCES tenant.tenants(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    department VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);

COMMENT ON TABLE clinical.receptionists IS 'Receptionist - Patient onboarding staff';
COMMENT ON COLUMN clinical.receptionists.user_id IS '1-to-1 link with auth.users (enforced even with soft-delete)';
COMMENT ON COLUMN clinical.receptionists.department IS 'Organizational department for filtering/reporting';

CREATE INDEX idx_receptionists_user_id ON clinical.receptionists(user_id);
CREATE INDEX idx_receptionists_tenant_id ON clinical.receptionists(tenant_id);
CREATE INDEX idx_receptionists_department ON clinical.receptionists(department);

-- Step 4: Add first_name and last_name to doctors table
ALTER TABLE clinical.doctors ADD COLUMN IF NOT EXISTS first_name VARCHAR(100);
ALTER TABLE clinical.doctors ADD COLUMN IF NOT EXISTS last_name VARCHAR(100);

-- Step 5: Migrate existing name data to first_name and last_name
-- Split on first space, everything before = first_name, everything after = last_name
UPDATE clinical.doctors
SET 
    first_name = SPLIT_PART(name, ' ', 1),
    last_name = CASE 
        WHEN POSITION(' ' IN name) > 0 THEN SUBSTRING(name FROM POSITION(' ' IN name) + 1)
        ELSE ''
    END
WHERE first_name IS NULL;

-- Step 6: Make first_name and last_name NOT NULL after migration
ALTER TABLE clinical.doctors ALTER COLUMN first_name SET NOT NULL;
ALTER TABLE clinical.doctors ALTER COLUMN last_name SET NOT NULL;

-- Step 7: Rename specialization to department
ALTER TABLE clinical.doctors RENAME COLUMN specialization TO department;

-- Step 8: Make department NOT NULL (was nullable as specialization)
-- First, set a default value for any NULL departments
UPDATE clinical.doctors SET department = 'General' WHERE department IS NULL;
ALTER TABLE clinical.doctors ALTER COLUMN department SET NOT NULL;

COMMENT ON COLUMN clinical.doctors.department IS 'Organizational department (renamed from specialization)';

-- Step 9: Make license_number nullable
ALTER TABLE clinical.doctors ALTER COLUMN license_number DROP NOT NULL;

COMMENT ON COLUMN clinical.doctors.license_number IS 'Medical license number - can be updated later by HOD/Admin';

-- Step 10: Drop the old name column
ALTER TABLE clinical.doctors DROP COLUMN IF EXISTS name;

-- Step 11: Add department field to invitations table (for staff role invitations)
ALTER TABLE auth.invitations ADD COLUMN IF NOT EXISTS department VARCHAR(255);

COMMENT ON COLUMN auth.invitations.department IS 'Required for HOD/DOCTOR/RECEPTIONIST invitations';
