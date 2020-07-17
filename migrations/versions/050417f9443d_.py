"""empty message

Revision ID: 050417f9443d
Revises: 2973363eeb50
Create Date: 2020-07-17 15:19:02.579097

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '050417f9443d'
down_revision = '2973363eeb50'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Application', sa.Column('terms_agreement', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Application', 'terms_agreement')
    # ### end Alembic commands ###
