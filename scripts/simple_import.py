#!/usr/bin/env python3
"""
Simple data import to Supabase
"""
import psycopg2
import psycopg2.extras
import os

# Connection details
supabase_conn = "postgresql://postgres:WealthPath2025@db.pxattzoxobqwkrwwtzae.supabase.co:5432/postgres"

# User data to import (from our export)
users_data = [
    (2, 'test@example.com_disabled', '$2b$12$vVPCMeVCaoY9oPvKFgwotufWvvxemcIuRGwwBQtDNcpPSh1jOg3AK', False, 'active', '2025-08-14 02:41:13.86927+00', None, None, None, None, None, None),
    (3, 'test@gmail.com', '$2b$12$z4/JcnAwGbnAE3L9YfOE6.SRwPAdvNDZkO9880DqHWuJber6zFWUi', True, 'active', '2025-08-21 22:17:05.031891+00', '2025-08-22 06:56:50.676065+00', None, None, 'test', 'test', None),
    (1, 'debashishroy@gmail.com', '$2b$12$8bZVnKiT.U.1ENFKi1K3JuU1EJvhccHJnmr.flegr36P9tgT/mT26', True, 'active', '2025-08-10 06:08:53.341584+00', '2025-08-24 01:24:51.507232+00', None, None, 'Debashish', 'Roy', None),
    (4, 'test1@gmail.com', '$2b$12$ysPQMZihf5p65H6HNB8mreQnXLkzNY.0o3eefev4FPkPlLpumIAaa', True, 'active', '2025-08-24 01:34:04.40313+00', None, None, None, 'test1', 'test1', None),
    (5, 'test@example.com', '$2b$12$NaHSjNiBsNcz6buth/heHeHXsBhkiHgc1BwA2/jBt9fYFQp8g5tei', True, 'active', '2025-08-26 14:32:02.281262+00', None, None, None, 'Test', 'User', None),
    (6, 'testuser@gmail.com', '$2b$12$cxDSGOdNXny1FzFDfYIqSu8CsOEZiUoZbxWenFciovw7YIj79a.Ei', True, 'active', '2025-08-29 14:37:00.882559+00', None, None, None, 'Test', 'User', None),
    (7, 'test1@example.com', '$2b$12$9cqd69Fchi4ulDUDCUB.I.2afmpjFrqyx4oa6IxxetyRLTMYg/gdi', True, 'active', '2025-08-29 20:48:17.791499+00', None, None, None, 'Test', 'User1', None),
    (8, 'testuser@example.com', '$2b$12$b6xqJ4UZaQmKL/1rWS.nZ.fl1ynjn3YorcnZyST1QdSX7CwfN1WLi', True, 'active', '2025-09-06 17:46:20.296293+00', None, None, None, 'Test', 'User', None),
]

user_profiles_data = [
    (2, 2, None, '5', None, '2025-08-14 02:41:14.10613+00', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None),
    (1, 1, None, 'moderate', 'employed', '2025-08-10 06:08:53.580742+00', '2025-08-20 06:19:47.977291+00', 54, None, 'married', 'NC', None, 'IT Consultant', None, None, None, None, None, None, 'Name: DR', None, None, None, None, None, None, None),
    (3, 3, None, 'aggressive', 'employed', '2025-08-21 22:18:42.937938+00', '2025-08-21 22:19:28.272503+00', 40, None, 'married', 'NJ', 'USA', 'Software Engineer', None, None, None, None, None, None, None, None, None, 6, 67, None, None, '{}'),
    (4, 4, None, None, None, '2025-08-24 01:34:36.642023+00', None, None, None, None, None, 'USA', None, None, None, None, None, None, None, None, None, None, 6, 67, None, None, '{}'),
]

user_benefits_data = [
    (2, 3, 'social_security', 'Social Security', 2000.00, None, None, None, False, None, None, None, None, None, False, None, None, None, None, None, None, None, '2025-08-21 22:21:07.792177+00', None, None, None, None, None, None, None, None),
    (1, 1, 'social_security', 'Primary Social Security', 4005.00, 67, None, None, False, None, None, None, None, None, False, None, None, None, None, None, None, '4000', '2025-08-20 02:57:57.828367+00', '2025-09-06 17:02:43.805053+00', None, None, None, None, None, None, None),
    (3, 1, '401k', '401(k) Plan', None, None, None, None, False, None, None, None, None, None, False, None, None, None, 250000.00, None, None, None, '2025-09-06 16:52:08.747162+00', '2025-09-06 18:11:15.431689+00', None, None, '100% up to 3%', '25% per year starting year 1', None, None, 30500.00),
    (4, 3, '401k', '401(k) Plan', None, None, None, None, False, None, None, None, None, None, False, None, None, None, 125000.00, None, None, None, '2025-09-06 17:50:45.976373+00', '2025-09-06 23:39:14.687116+00', None, None, '100% up to 3%', 'immediate', None, None, 23000.00),
]

user_estate_planning_data = [
    (3, 1, 'beneficiary_designation', 'Beneficiary Designation DR', 'current', '2025-08-28', None, 'Smith & Associate Law firm', None, '{}', '2025-08-29 02:18:39.836531+00', '2025-08-29 02:18:39.836531+00'),
    (4, 1, 'healthcare_directive', 'DR Healthcare Directive', 'current', '2025-08-28', None, 'Smith', None, '{}', '2025-08-29 02:21:24.589549+00', '2025-08-29 02:21:24.589549+00'),
    (5, 1, 'will', 'DR Will', 'current', '2025-08-28', '2026-08-28', None, None, '{}', '2025-08-29 02:47:28.822995+00', '2025-08-29 02:47:28.822995+00'),
    (6, 1, 'power_of_attorney', 'DR POA', 'current', '2025-08-28', '2027-08-28', None, None, '{}', '2025-08-29 02:47:55.750293+00', '2025-08-29 02:47:55.750293+00'),
]

user_insurance_policies_data = [
    (3, 1, 'auto', 'Auto Insurance', 50000.00, 1400.00, 'AR', None, '{}', '2025-08-28 23:44:14.032056+00', '2025-08-28 23:44:27.549125+00'),
    (4, 1, 'homeowners', 'Home Insurance', 800000.00, 1300.00, 'AR', None, '{}', '2025-08-28 23:54:17.474322+00', '2025-08-28 23:54:17.474322+00'),
]

user_investment_preferences_data = [
    (1, 1, 7, 15, 'annual', 'balanced', 1, 10.00, 50.0, None, 0.0, True, True, None, '2025-08-29 02:42:14.448118+00', '2025-08-29 05:10:33.912568+00'),
]

def main():
    print("Starting Supabase Data Import")
    print("=" * 50)
    
    try:
        # Connect to Supabase
        conn = psycopg2.connect(supabase_conn)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("Connected to Supabase successfully")
        
        # Import users
        print("Importing users...")
        cursor.executemany("""
            INSERT INTO users (id, email, password_hash, email_verified, status, created_at, last_login, deleted_at, refresh_token, first_name, last_name, profile_image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                password_hash = EXCLUDED.password_hash,
                email_verified = EXCLUDED.email_verified,
                status = EXCLUDED.status,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name
        """, users_data)
        print(f"   Imported {len(users_data)} users")
        
        # Import user profiles  
        print("Importing user profiles...")
        cursor.executemany("""
            INSERT INTO user_profiles (id, user_id, phone_number, risk_tolerance, employment_status, created_at, updated_at, age, date_of_birth, marital_status, state, country, occupation, annual_income, monthly_expenses, net_worth, financial_goals, investment_experience, time_horizon, notes, emergency_fund, retirement_savings, risk_tolerance_score, retirement_age, dependents_count, tax_filing_status, additional_info)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                phone_number = EXCLUDED.phone_number,
                risk_tolerance = EXCLUDED.risk_tolerance,
                employment_status = EXCLUDED.employment_status,
                age = EXCLUDED.age,
                marital_status = EXCLUDED.marital_status,
                state = EXCLUDED.state,
                occupation = EXCLUDED.occupation,
                updated_at = EXCLUDED.updated_at
        """, user_profiles_data)
        print(f"   Imported {len(user_profiles_data)} user profiles")
        
        # Import user benefits
        print("📊 Importing user benefits...")
        cursor.executemany("""
            INSERT INTO user_benefits (id, user_id, benefit_type, benefit_name, estimated_monthly_benefit, claiming_age, benefit_start_date, benefit_end_date, is_active, spouse_benefit_amount, spouse_claiming_age, survivor_benefit_percentage, disability_benefit_amount, medicare_part_b_premium, has_medicare_supplement, supplemental_insurance_cost, long_term_care_coverage, long_term_care_premium, current_balance, annual_contribution, employer_match_percentage, social_security_estimated_benefit, created_at, updated_at, vesting_schedule, contribution_limits, employer_401k_match_formula, employer_401k_vesting_schedule, pension_monthly_benefit, pension_start_age, annual_employer_contribution)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                benefit_name = EXCLUDED.benefit_name,
                estimated_monthly_benefit = EXCLUDED.estimated_monthly_benefit,
                claiming_age = EXCLUDED.claiming_age,
                current_balance = EXCLUDED.current_balance,
                updated_at = EXCLUDED.updated_at
        """, user_benefits_data)
        print(f"   ✅ Imported {len(user_benefits_data)} user benefits")
        
        # Import user estate planning
        print("📊 Importing user estate planning...")
        cursor.executemany("""
            INSERT INTO user_estate_planning (id, user_id, document_type, document_name, status, last_updated, next_review_date, attorney_contact, document_location, document_details, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                document_name = EXCLUDED.document_name,
                status = EXCLUDED.status,
                attorney_contact = EXCLUDED.attorney_contact,
                updated_at = EXCLUDED.updated_at
        """, user_estate_planning_data)
        print(f"   ✅ Imported {len(user_estate_planning_data)} estate planning documents")
        
        # Import user insurance policies
        print("📊 Importing user insurance policies...")
        cursor.executemany("""
            INSERT INTO user_insurance_policies (id, user_id, policy_type, policy_name, coverage_amount, annual_premium, beneficiary_primary, beneficiary_secondary, policy_details, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                policy_name = EXCLUDED.policy_name,
                coverage_amount = EXCLUDED.coverage_amount,
                annual_premium = EXCLUDED.annual_premium,
                updated_at = EXCLUDED.updated_at
        """, user_insurance_policies_data)
        print(f"   ✅ Imported {len(user_insurance_policies_data)} insurance policies")
        
        # Import user investment preferences
        print("📊 Importing user investment preferences...")
        cursor.executemany("""
            INSERT INTO user_investment_preferences (id, user_id, risk_tolerance_score, investment_timeline_years, rebalancing_frequency, investment_philosophy, esg_preference_level, international_allocation_target, alternative_investment_interest, cryptocurrency_allocation, individual_stock_tolerance, tax_loss_harvesting_enabled, dollar_cost_averaging_preference, sector_preferences, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                risk_tolerance_score = EXCLUDED.risk_tolerance_score,
                investment_timeline_years = EXCLUDED.investment_timeline_years,
                rebalancing_frequency = EXCLUDED.rebalancing_frequency,
                updated_at = EXCLUDED.updated_at
        """, user_investment_preferences_data)
        print(f"   ✅ Imported {len(user_investment_preferences_data)} investment preferences")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 Migration completed successfully!")
        print("📊 Summary:")
        print(f"   - {len(users_data)} users")
        print(f"   - {len(user_profiles_data)} user profiles") 
        print(f"   - {len(user_benefits_data)} user benefits")
        print(f"   - {len(user_estate_planning_data)} estate planning documents")
        print(f"   - {len(user_insurance_policies_data)} insurance policies")
        print(f"   - {len(user_investment_preferences_data)} investment preferences")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()