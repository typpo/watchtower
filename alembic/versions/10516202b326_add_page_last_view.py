"""add page.last_view

Revision ID: 10516202b326
Revises: None
Create Date: 2013-03-04 12:45:13.010491

"""

# revision identifiers, used by Alembic.
revision = '10516202b326'
down_revision = None

from alembic import op
import sqlalchemy as sa
from datetime import datetime


def upgrade():
    op.add_column('page', sa.Column('last_view', sa.DateTime, default=datetime.now()))


def downgrade():
    pass
