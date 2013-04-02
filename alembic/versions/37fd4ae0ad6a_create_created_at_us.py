"""create created_at user col

Revision ID: 37fd4ae0ad6a
Revises: 4e43a0ab95dc
Create Date: 2013-04-01 20:57:05.374621

"""

# revision identifiers, used by Alembic.
revision = '37fd4ae0ad6a'
down_revision = '4e43a0ab95dc'

from alembic import op
import sqlalchemy as sa
from datetime import datetime


def upgrade():
    op.add_column('user', sa.Column('created_at', sa.DateTime, default=datetime.now))


def downgrade():
    op.drop_column('user', 'created_at')
