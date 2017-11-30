"""empty message

Revision ID: a8d4e8a4f31e
Revises: cb2c7f3dece0
Create Date: 2017-11-23 12:15:09.360006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8d4e8a4f31e'
down_revision = 'cb2c7f3dece0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('room', sa.Column('reward', sa.Integer(), nullable=True))
    op.drop_column('room', 'score')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('room', sa.Column('score', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('room', 'reward')
    # ### end Alembic commands ###