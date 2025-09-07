"""Add missing social security fields to user_benefits

Revision ID: social_security_fix
Revises: 0ae4f242fecf
Create Date: 2025-01-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'social_security_fix'
down_revision = '0ae4f242fecf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing social security fields to user_benefits table (with duplicate check)
    connection = op.get_bind()
    
    # Check if columns exist before adding
    try:
        connection.execute(sa.text("""
            ALTER TABLE user_benefits 
            ADD COLUMN IF NOT EXISTS social_security_estimated_benefit NUMERIC(8, 2)
        """))
    except Exception:
        pass
    
    try:
        connection.execute(sa.text("""
            ALTER TABLE user_benefits 
            ADD COLUMN IF NOT EXISTS social_security_claiming_age INTEGER
        """))
    except Exception:
        pass


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('user_benefits', 'social_security_claiming_age')
    op.drop_column('user_benefits', 'social_security_estimated_benefit')