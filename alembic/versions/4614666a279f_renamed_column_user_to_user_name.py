"""renamed column user to user_name

Revision ID: 4614666a279f
Revises: 578b43a08697
Create Date: 2015-06-29 20:44:11.117613

"""

# revision identifiers, used by Alembic.
revision = '4614666a279f'
down_revision = '578b43a08697'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.alter_column('definitions', 'user', new_column_name='user_name', existing_type=sa.Unicode(255))
    op.alter_column('interactions', 'user', new_column_name='user_name', existing_type=sa.Unicode(255))


def downgrade():
    op.alter_column('definitions', 'user_name', new_column_name='user', existing_type=sa.Unicode(255))
    op.alter_column('interactions', 'user_name', new_column_name='user', existing_type=sa.Unicode(255))
