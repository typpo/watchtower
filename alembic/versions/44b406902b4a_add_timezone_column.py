"""add timezone column

Revision ID: 44b406902b4a
Revises: 42d527d69f2c
Create Date: 2013-03-10 21:49:27.417863

"""

# revision identifiers, used by Alembic.
revision = '44b406902b4a'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('timezone', sa.String(64), default='America/Los_Angeles'))

def downgrade():
    op.drop_column('user', 'timezone')
