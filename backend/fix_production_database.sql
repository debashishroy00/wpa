-- Fix production database missing columns for user_benefits table
-- Execute this SQL directly in the production database

-- Add missing columns that are causing the SQLAlchemy error
-- These columns exist in the model but are missing from production database

ALTER TABLE user_benefits 
ADD COLUMN IF NOT EXISTS social_security_estimated_benefit NUMERIC(8, 2);

ALTER TABLE user_benefits 
ADD COLUMN IF NOT EXISTS social_security_claiming_age INTEGER;

ALTER TABLE user_benefits 
ADD COLUMN IF NOT EXISTS employer_401k_match_formula VARCHAR(200);

ALTER TABLE user_benefits 
ADD COLUMN IF NOT EXISTS employer_401k_vesting_schedule VARCHAR(200);

ALTER TABLE user_benefits 
ADD COLUMN IF NOT EXISTS max_401k_contribution NUMERIC(12, 2);

ALTER TABLE user_benefits 
ADD COLUMN IF NOT EXISTS pension_details TEXT;

ALTER TABLE user_benefits 
ADD COLUMN IF NOT EXISTS other_benefits TEXT;

ALTER TABLE user_benefits 
ADD COLUMN IF NOT EXISTS notes TEXT;

-- Verify the columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'user_benefits' 
ORDER BY column_name;