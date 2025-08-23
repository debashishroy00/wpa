"""merge heads

Revision ID: f96632089afd
Revises: 306ad2796314, fix_data_integrity_001
Create Date: 2025-08-21 16:01:26.646669

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f96632089afd'
down_revision = ('306ad2796314', 'fix_data_integrity_001')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass