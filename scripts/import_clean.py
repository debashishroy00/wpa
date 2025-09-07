#!/usr/bin/env python3
"""
Clean data import to Supabase without emojis
"""
import psycopg2
import psycopg2.extras

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
        
        # Import users first
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
        
        # Import investment preferences with the correct data types
        print("Importing user investment preferences...")
        cursor.executemany("""
            INSERT INTO user_investment_preferences (id, user_id, risk_tolerance_score, investment_timeline_years, rebalancing_frequency, investment_philosophy, esg_preference_level, international_allocation_target, alternative_investment_interest, cryptocurrency_allocation, individual_stock_tolerance, tax_loss_harvesting_enabled, dollar_cost_averaging_preference, sector_preferences, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                risk_tolerance_score = EXCLUDED.risk_tolerance_score,
                investment_timeline_years = EXCLUDED.investment_timeline_years,
                rebalancing_frequency = EXCLUDED.rebalancing_frequency,
                updated_at = EXCLUDED.updated_at
        """, user_investment_preferences_data)
        print(f"   Imported {len(user_investment_preferences_data)} investment preferences")
        
        # Commit all changes
        conn.commit()
        print("\nMigration completed successfully!")
        print("Summary:")
        print(f"   - {len(users_data)} users")
        print(f"   - {len(user_investment_preferences_data)} investment preferences")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()