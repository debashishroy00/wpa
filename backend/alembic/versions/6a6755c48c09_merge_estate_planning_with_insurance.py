"""merge estate planning with insurance

Revision ID: 6a6755c48c09
Revises: 2b1dc9619eda, add_estate_planning
Create Date: 2025-08-28 23:58:43.318014

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a6755c48c09'
down_revision = ('2b1dc9619eda', 'add_estate_planning')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass