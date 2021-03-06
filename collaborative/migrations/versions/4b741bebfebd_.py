"""empty message

Revision ID: 4b741bebfebd
Revises: 620620963fdc
Create Date: 2017-11-23 15:43:21.615986

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '4b741bebfebd'
down_revision = '620620963fdc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('room', sa.Column('p1_scores', sqlalchemy_utils.types.scalar_list.ScalarListType(), nullable=True))
    op.add_column('room', sa.Column('p2_scores', sqlalchemy_utils.types.scalar_list.ScalarListType(), nullable=True))
    op.drop_column('room', 'next_game_bool')
    op.drop_column('room', 'scores')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('room', sa.Column('scores', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('room', sa.Column('next_game_bool', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('room', 'p2_scores')
    op.drop_column('room', 'p1_scores')
    # ### end Alembic commands ###
