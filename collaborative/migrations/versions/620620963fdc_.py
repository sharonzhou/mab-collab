"""empty message

Revision ID: 620620963fdc
Revises: a8d4e8a4f31e
Create Date: 2017-11-23 14:32:52.598763

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision = '620620963fdc'
down_revision = 'a8d4e8a4f31e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('room', sa.Column('completion_code', sa.String(length=1024), nullable=True))
    op.add_column('room', sa.Column('next_game_bool', sa.Boolean(), nullable=True))
    op.add_column('room', sa.Column('scores', sqlalchemy_utils.types.scalar_list.ScalarListType(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('room', 'scores')
    op.drop_column('room', 'next_game_bool')
    op.drop_column('room', 'completion_code')
    # ### end Alembic commands ###
