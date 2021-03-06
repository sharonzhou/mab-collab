"""empty message

Revision ID: 037359269124
Revises: 569a6a4735f6
Create Date: 2017-11-30 01:54:15.259962

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '037359269124'
down_revision = '569a6a4735f6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('room', sa.Column('dropout', sa.Boolean(), nullable=True))
    op.add_column('worker', sa.Column('timeout', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('worker', 'timeout')
    op.drop_column('room', 'dropout')
    # ### end Alembic commands ###
