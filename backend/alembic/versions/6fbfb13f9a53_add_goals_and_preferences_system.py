"""add_goals_and_preferences_system

Revision ID: 6fbfb13f9a53
Revises: 759dfa32e81b
Create Date: 2025-08-14 02:12:21.536322

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '6fbfb13f9a53'
down_revision = '759dfa32e81b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable UUID extension if not already enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    
    # 2. Create goals table
    op.create_table('goals',
        sa.Column('goal_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('target_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('target_date', sa.Date, nullable=False),
        sa.Column('priority', sa.Integer, nullable=False, default=3),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('params', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('priority >= 1 AND priority <= 10', name='valid_priority'),
        sa.CheckConstraint('target_amount >= 0', name='positive_target_amount'),
        sa.CheckConstraint("status IN ('active', 'paused', 'achieved', 'cancelled')", name='valid_status'),
        sa.CheckConstraint("category IN ('retirement', 'education', 'real_estate', 'business', 'travel', 'emergency_fund', 'debt_payoff', 'major_purchase', 'other')", name='valid_category')
    )
    
    # 3. Create goals_history table for audit trail
    op.create_table('goals_history',
        sa.Column('history_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('goal_id', UUID(as_uuid=True), sa.ForeignKey('goals.goal_id', ondelete='CASCADE'), nullable=False),
        sa.Column('changed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('change_type', sa.String(20), nullable=False),
        sa.Column('reason', sa.String(500)),
        sa.Column('diff', JSONB, nullable=False),
        sa.Column('actor', sa.String(255), nullable=False),
        sa.CheckConstraint("change_type IN ('created', 'updated', 'deleted', 'achieved', 'paused', 'resumed')", name='valid_change_type')
    )
    
    # 4. Create goal_relationships table
    op.create_table('goal_relationships',
        sa.Column('relationship_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('parent_goal_id', UUID(as_uuid=True), sa.ForeignKey('goals.goal_id', ondelete='CASCADE'), nullable=False),
        sa.Column('child_goal_id', UUID(as_uuid=True), sa.ForeignKey('goals.goal_id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("relationship_type IN ('depends_on', 'conflicts_with', 'enables', 'part_of')", name='valid_relationship_type'),
        sa.UniqueConstraint('parent_goal_id', 'child_goal_id', 'relationship_type', name='unique_goal_relationship')
    )
    
    # 5. Create goal_progress table
    op.create_table('goal_progress',
        sa.Column('progress_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('goal_id', UUID(as_uuid=True), sa.ForeignKey('goals.goal_id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('percentage_complete', sa.Numeric(5, 2), nullable=False),
        sa.Column('recorded_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('notes', sa.Text),
        sa.Column('source', sa.String(50), nullable=False, default='manual'),
        sa.CheckConstraint('current_amount >= 0', name='positive_current_amount'),
        sa.CheckConstraint('percentage_complete >= 0 AND percentage_complete <= 100', name='valid_percentage'),
        sa.CheckConstraint("source IN ('manual', 'calculated', 'imported')", name='valid_source')
    )
    
    # 6. Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('preference_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('risk_tolerance', sa.String(20), nullable=False, default='moderate'),
        sa.Column('investment_timeline', sa.Integer, nullable=False, default=20),
        sa.Column('financial_knowledge', sa.String(20), nullable=False, default='intermediate'),
        sa.Column('retirement_age', sa.Integer),
        sa.Column('annual_income_goal', sa.Numeric(18, 2)),
        sa.Column('emergency_fund_months', sa.Integer, nullable=False, default=6),
        sa.Column('debt_payoff_priority', sa.String(20), nullable=False, default='balanced'),
        sa.Column('notification_preferences', JSONB, nullable=False, server_default='{}'),
        sa.Column('goal_categories_enabled', JSONB, nullable=False, server_default='["retirement", "emergency_fund", "education", "real_estate"]'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("risk_tolerance IN ('conservative', 'moderate', 'aggressive')", name='valid_risk_tolerance'),
        sa.CheckConstraint("financial_knowledge IN ('beginner', 'intermediate', 'advanced')", name='valid_financial_knowledge'),
        sa.CheckConstraint("debt_payoff_priority IN ('avalanche', 'snowball', 'balanced')", name='valid_debt_strategy'),
        sa.CheckConstraint('investment_timeline >= 1 AND investment_timeline <= 50', name='valid_timeline'),
        sa.CheckConstraint('retirement_age >= 50 AND retirement_age <= 80', name='valid_retirement_age'),
        sa.CheckConstraint('emergency_fund_months >= 1 AND emergency_fund_months <= 12', name='valid_emergency_months')
    )
    
    # 7. Create indexes for performance
    op.create_index('idx_goals_user_status', 'goals', ['user_id', 'status'])
    op.create_index('idx_goals_category', 'goals', ['category'])
    op.create_index('idx_goals_target_date', 'goals', ['target_date'])
    op.create_index('idx_goals_priority', 'goals', ['priority'])
    op.create_index('idx_goals_history_goal_id', 'goals_history', ['goal_id'])
    op.create_index('idx_goals_history_changed_at', 'goals_history', ['changed_at'])
    op.create_index('idx_goal_progress_goal_id', 'goal_progress', ['goal_id'])
    op.create_index('idx_goal_progress_recorded_at', 'goal_progress', ['recorded_at'])
    
    # 8. Create audit trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_goal_changes()
        RETURNS TRIGGER AS $$
        DECLARE
            change_reason TEXT;
            actor_name TEXT;
            old_data JSONB;
            new_data JSONB;
            diff_data JSONB;
        BEGIN
            -- Get change reason from session variable
            SELECT current_setting('wpa.change_reason', true) INTO change_reason;
            IF change_reason IS NULL OR change_reason = '' THEN
                change_reason := 'System change';
            END IF;
            
            -- Get actor from session variable
            SELECT current_setting('wpa.actor', true) INTO actor_name;
            IF actor_name IS NULL OR actor_name = '' THEN
                actor_name := 'System';
            END IF;
            
            IF TG_OP = 'DELETE' THEN
                old_data := to_jsonb(OLD);
                INSERT INTO goals_history (goal_id, change_type, reason, diff, actor)
                VALUES (OLD.goal_id, 'deleted', change_reason, old_data, actor_name);
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                old_data := to_jsonb(OLD);
                new_data := to_jsonb(NEW);
                
                -- Calculate diff
                diff_data := jsonb_build_object(
                    'old', old_data,
                    'new', new_data
                );
                
                -- Update the updated_at timestamp
                NEW.updated_at := NOW();
                
                INSERT INTO goals_history (goal_id, change_type, reason, diff, actor)
                VALUES (NEW.goal_id, 'updated', change_reason, diff_data, actor_name);
                RETURN NEW;
            ELSIF TG_OP = 'INSERT' THEN
                new_data := to_jsonb(NEW);
                INSERT INTO goals_history (goal_id, change_type, reason, diff, actor)
                VALUES (NEW.goal_id, 'created', change_reason, new_data, actor_name);
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # 9. Create trigger on goals table
    op.execute("""
        CREATE TRIGGER goals_audit_trigger
            AFTER INSERT OR UPDATE OR DELETE ON goals
            FOR EACH ROW EXECUTE FUNCTION audit_goal_changes();
    """)
    
    # 10. Create function to calculate goal progress percentage
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_goal_progress_percentage()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Calculate percentage based on current_amount and target_amount
            SELECT 
                CASE 
                    WHEN g.target_amount > 0 THEN 
                        ROUND((NEW.current_amount / g.target_amount) * 100, 2)
                    ELSE 0 
                END INTO NEW.percentage_complete
            FROM goals g 
            WHERE g.goal_id = NEW.goal_id;
            
            -- Auto-achieve goal if 100% complete
            IF NEW.percentage_complete >= 100 THEN
                UPDATE goals 
                SET status = 'achieved' 
                WHERE goal_id = NEW.goal_id AND status = 'active';
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # 11. Create trigger for progress calculation
    op.execute("""
        CREATE TRIGGER goal_progress_calculation_trigger
            BEFORE INSERT OR UPDATE ON goal_progress
            FOR EACH ROW EXECUTE FUNCTION calculate_goal_progress_percentage();
    """)
    
    # 12. Create function to detect goal conflicts
    op.execute("""
        CREATE OR REPLACE FUNCTION find_goal_conflicts(target_user_id INTEGER)
        RETURNS TABLE(
            goal1_id UUID,
            goal1_name TEXT,
            goal2_id UUID, 
            goal2_name TEXT,
            conflict_type TEXT,
            severity TEXT
        ) AS $$
        BEGIN
            RETURN QUERY
            -- Same target date conflicts
            SELECT 
                g1.goal_id, g1.name,
                g2.goal_id, g2.name,
                'same_deadline'::TEXT,
                'medium'::TEXT
            FROM goals g1, goals g2
            WHERE g1.user_id = target_user_id 
                AND g2.user_id = target_user_id
                AND g1.goal_id < g2.goal_id
                AND g1.target_date = g2.target_date
                AND g1.status = 'active'
                AND g2.status = 'active'
                
            UNION ALL
            
            -- Overlapping high-priority goals
            SELECT 
                g1.goal_id, g1.name,
                g2.goal_id, g2.name,
                'priority_conflict'::TEXT,
                'high'::TEXT
            FROM goals g1, goals g2
            WHERE g1.user_id = target_user_id 
                AND g2.user_id = target_user_id
                AND g1.goal_id < g2.goal_id
                AND g1.priority <= 2
                AND g2.priority <= 2
                AND ABS(EXTRACT(EPOCH FROM (g1.target_date - g2.target_date))/86400) <= 365
                AND g1.status = 'active'
                AND g2.status = 'active';
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # 13. Create function to update user preferences timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_preferences_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at := NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # 14. Create trigger for preferences updates
    op.execute("""
        CREATE TRIGGER preferences_update_trigger
            BEFORE UPDATE ON user_preferences
            FOR EACH ROW EXECUTE FUNCTION update_preferences_timestamp();
    """)


def downgrade() -> None:
    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS preferences_update_trigger ON user_preferences")
    op.execute("DROP TRIGGER IF EXISTS goal_progress_calculation_trigger ON goal_progress")
    op.execute("DROP TRIGGER IF EXISTS goals_audit_trigger ON goals")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_preferences_timestamp()")
    op.execute("DROP FUNCTION IF EXISTS find_goal_conflicts(INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS calculate_goal_progress_percentage()")
    op.execute("DROP FUNCTION IF EXISTS audit_goal_changes()")
    
    # Drop indexes
    op.drop_index('idx_goal_progress_recorded_at')
    op.drop_index('idx_goal_progress_goal_id')
    op.drop_index('idx_goals_history_changed_at')
    op.drop_index('idx_goals_history_goal_id')
    op.drop_index('idx_goals_priority')
    op.drop_index('idx_goals_target_date')
    op.drop_index('idx_goals_category')
    op.drop_index('idx_goals_user_status')
    
    # Drop tables in reverse order
    op.drop_table('user_preferences')
    op.drop_table('goal_progress')
    op.drop_table('goal_relationships')
    op.drop_table('goals_history')
    op.drop_table('goals')