"""merge insurance migration

Revision ID: 2b1dc9619eda
Revises: 1444dadba9de, add_insurance_policies
Create Date: 2025-08-28 23:28:05.641271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b1dc9619eda'
down_revision = ('1444dadba9de', 'add_insurance_policies')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass