"""empty message

Revision ID: 3975622d1054
Revises: 
Create Date: 2017-11-19 16:19:31.414723

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3975622d1054'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('move', sa.Column('score', sa.Integer(), nullable=True))
    op.add_column('room', sa.Column('score', sa.Integer(), nullable=True))
    op.add_column('room', sa.Column('time_last_move', sa.DateTime(), nullable=True))
    op.alter_column('room', 'next_turn_uid',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_column('room', 'reward')
    op.add_column('worker', sa.Column('is_ready', sa.Boolean(), nullable=True))
    op.add_column('worker', sa.Column('room_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('worker', 'room_id')
    op.drop_column('worker', 'is_ready')
    op.add_column('room', sa.Column('reward', sa.INTEGER(), autoincrement=False, nullable=True))
    op.alter_column('room', 'next_turn_uid',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('room', 'time_last_move')
    op.drop_column('room', 'score')
    op.drop_column('move', 'score')
    # ### end Alembic commands ###
