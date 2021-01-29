"""empty message

Revision ID: 12a9fdc66317
Revises: 80530ea60e18
Create Date: 2021-01-28 00:55:12.438138

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12a9fdc66317'
down_revision = '80530ea60e18'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('audio_setup', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'audio_setup')
    # ### end Alembic commands ###