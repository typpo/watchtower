"""add password column

Revision ID: 42d527d69f2c
Revises: 10516202b326
Create Date: 2013-03-05 10:31:53.533688

"""

# revision identifiers, used by Alembic.
revision = '42d527d69f2c'
down_revision = '10516202b326'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('password', sa.String(255), default='cune8eVE'))

def downgrade():
    pass
