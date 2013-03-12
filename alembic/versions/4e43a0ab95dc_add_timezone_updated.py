"""Add timezone (updated revision post-undo-projects)

Revision ID: 4e43a0ab95dc
Revises: None
Create Date: 2013-03-11 19:52:22.626168

"""

# revision identifiers, used by Alembic.
revision = '4e43a0ab95dc'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('timezone', sa.String(64), default='America/Los_Angeles'))

def downgrade():
    #op.drop_column('user', 'timezone')
    pass
