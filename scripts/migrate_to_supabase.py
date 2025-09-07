#!/usr/bin/env python3
"""
WealthPath AI - Data Migration Script
Migrates user data from local PostgreSQL to Supabase production database
"""
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles migration from local PostgreSQL to Supabase"""
    
    def __init__(self):
        # Local PostgreSQL connection
        self.local_db = {
            'host': os.getenv('LOCAL_PG_HOST', 'localhost'),
            'database': os.getenv('LOCAL_PG_DATABASE', 'wealthpath_db'),
            'user': os.getenv('LOCAL_PG_USER', 'postgres'),
            'password': os.getenv('LOCAL_PG_PASSWORD', 'password'),
            'port': os.getenv('LOCAL_PG_PORT', '5432')
        }
        
        # Supabase connection (from S1.png connection string)
        supabase_url = os.getenv('SUPABASE_DATABASE_URL')
        if not supabase_url:
            raise ValueError("SUPABASE_DATABASE_URL environment variable required")
        
        # Parse Supabase URL
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(supabase_url)
        self.supabase_db = {
            'host': parsed.hostname,
            'database': parsed.path[1:],  # Remove leading /
            'user': parsed.username,
            'password': parsed.password,
            'port': parsed.port or 5432,
            'sslmode': 'require'
        }
        
        # Tables to migrate in dependency order
        self.migration_order = [
            'users',
            'user_profiles', 
            'user_benefits',
            'user_investment_preferences',
            'user_estate_planning',
            'user_insurance_policies',
            'user_goals',
            'user_tax_info',
            'user_debt_info',
            'user_assets',
            'conversation_history',
            'simple_vector_store'
        ]
    
    @contextmanager
    def get_connection(self, db_config: Dict[str, Any]):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(**db_config)
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def check_connections(self) -> bool:
        """Test both database connections"""
        logger.info("Testing database connections...")
        
        try:
            with self.get_connection(self.local_db) as local_conn:
                with local_conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    logger.info(f"Local PostgreSQL connection OK: {version}")
        except Exception as e:
            logger.error(f"Failed to connect to local PostgreSQL: {e}")
            return False
        
        try:
            with self.get_connection(self.supabase_db) as supabase_conn:
                with supabase_conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    logger.info(f"Supabase connection OK: {version}")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False
        
        return True
    
    def get_table_schema(self, conn, table_name: str) -> List[Dict]:
        """Get table column information"""
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            return cursor.fetchall()
    
    def table_exists(self, conn, table_name: str) -> bool:
        """Check if table exists"""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            return cursor.fetchone()[0]
    
    def get_row_count(self, conn, table_name: str) -> int:
        """Get total row count for a table"""
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            return cursor.fetchone()[0]
    
    def migrate_table(self, table_name: str, dry_run: bool = True) -> bool:
        """Migrate a single table from local to Supabase"""
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Migrating table: {table_name}")
        
        try:
            with self.get_connection(self.local_db) as local_conn, \
                 self.get_connection(self.supabase_db) as supabase_conn:
                
                # Check if table exists in both databases
                if not self.table_exists(local_conn, table_name):
                    logger.warning(f"Table {table_name} does not exist in local database, skipping")
                    return True
                
                if not self.table_exists(supabase_conn, table_name):
                    logger.warning(f"Table {table_name} does not exist in Supabase, skipping")
                    return True
                
                # Get row counts
                local_count = self.get_row_count(local_conn, table_name)
                supabase_count = self.get_row_count(supabase_conn, table_name)
                
                logger.info(f"Local rows: {local_count}, Supabase rows: {supabase_count}")
                
                if local_count == 0:
                    logger.info(f"No data to migrate for {table_name}")
                    return True
                
                # Get table schema to build proper INSERT statement
                local_schema = self.get_table_schema(local_conn, table_name)
                column_names = [col['column_name'] for col in local_schema]
                
                # Fetch all data from local table
                with local_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(f"SELECT * FROM {table_name} ORDER BY id;")
                    local_data = cursor.fetchall()
                
                if not local_data:
                    logger.info(f"No data found in local {table_name}")
                    return True
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would migrate {len(local_data)} rows to {table_name}")
                    if local_data:
                        logger.info(f"[DRY RUN] Sample data: {dict(local_data[0])}")
                    return True
                
                # Perform actual migration
                migrated_count = 0
                batch_size = 100
                
                for i in range(0, len(local_data), batch_size):
                    batch = local_data[i:i + batch_size]
                    
                    # Build INSERT statement with ON CONFLICT handling
                    placeholders = ', '.join(['%s'] * len(column_names))
                    columns_str = ', '.join(column_names)
                    
                    # Handle conflicts by updating existing records
                    update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in column_names if col != 'id'])
                    
                    insert_sql = f"""
                        INSERT INTO {table_name} ({columns_str})
                        VALUES ({placeholders})
                        ON CONFLICT (id) DO UPDATE SET {update_clause}
                    """
                    
                    with supabase_conn.cursor() as supabase_cursor:
                        # Prepare data for batch insert
                        batch_data = []
                        for row in batch:
                            row_data = [row.get(col) for col in column_names]
                            batch_data.append(row_data)
                        
                        supabase_cursor.executemany(insert_sql, batch_data)
                        migrated_count += supabase_cursor.rowcount
                
                supabase_conn.commit()
                logger.info(f"Successfully migrated {migrated_count} rows to {table_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            return False
    
    def migrate_all_tables(self, dry_run: bool = True) -> bool:
        """Migrate all tables in the correct order"""
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Starting full database migration")
        
        success_count = 0
        total_tables = len(self.migration_order)
        
        for table_name in self.migration_order:
            if self.migrate_table(table_name, dry_run):
                success_count += 1
            else:
                logger.error(f"Migration failed for table: {table_name}")
                if not dry_run:
                    response = input(f"Continue with remaining tables? (y/N): ")
                    if response.lower() != 'y':
                        break
        
        logger.info(f"Migration completed: {success_count}/{total_tables} tables successful")
        return success_count == total_tables
    
    def backup_supabase_data(self) -> bool:
        """Create a backup of current Supabase data before migration"""
        logger.info("Creating backup of Supabase data...")
        
        backup_file = f"supabase_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        try:
            # Use pg_dump to create backup
            import subprocess
            
            # Build pg_dump command
            dump_cmd = [
                'pg_dump',
                f"--host={self.supabase_db['host']}",
                f"--port={self.supabase_db['port']}",
                f"--username={self.supabase_db['user']}",
                f"--dbname={self.supabase_db['database']}",
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                '--format=plain',
                f"--file={backup_file}"
            ]
            
            # Set password via environment
            env = os.environ.copy()
            env['PGPASSWORD'] = self.supabase_db['password']
            
            result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Backup created successfully: {backup_file}")
                return True
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

def main():
    """Main migration function"""
    print("WealthPath AI - Database Migration Tool")
    print("=" * 50)
    
    # Check required environment variables
    if not os.getenv('SUPABASE_DATABASE_URL'):
        print("Error: SUPABASE_DATABASE_URL environment variable is required")
        print("Set it to your Supabase connection string from S1.png")
        sys.exit(1)
    
    migrator = DatabaseMigrator()
    
    # Test connections
    if not migrator.check_connections():
        print("Connection test failed. Please check your database configurations.")
        sys.exit(1)
    
    print("\nMigration Options:")
    print("1. Dry run (preview what would be migrated)")
    print("2. Full migration with backup")
    print("3. Migrate specific table")
    print("4. Exit")
    
    while True:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            # Dry run
            migrator.migrate_all_tables(dry_run=True)
            
        elif choice == '2':
            # Full migration
            print("\n⚠️  WARNING: This will migrate data to production Supabase!")
            print("This will backup existing Supabase data first.")
            confirm = input("Are you sure you want to proceed? (type 'yes' to confirm): ")
            
            if confirm.lower() == 'yes':
                # Create backup first
                if migrator.backup_supabase_data():
                    migrator.migrate_all_tables(dry_run=False)
                else:
                    print("Migration cancelled due to backup failure")
            else:
                print("Migration cancelled")
                
        elif choice == '3':
            # Specific table migration
            table_name = input("Enter table name: ").strip()
            if table_name:
                dry_run = input("Dry run? (Y/n): ").strip().lower() != 'n'
                migrator.migrate_table(table_name, dry_run=dry_run)
                
        elif choice == '4':
            print("Exiting...")
            break
            
        else:
            print("Invalid option. Please select 1-4.")

if __name__ == "__main__":
    main()