"""Merge migration heads

Revision ID: 13d03a2c7e3b
Revises: prod_benefits_fix, prod_fix_2025
Create Date: 2025-09-07 04:23:16.183682

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13d03a2c7e3b'
down_revision = ('prod_benefits_fix', 'prod_fix_2025')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass