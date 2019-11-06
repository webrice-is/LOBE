"""empty message

Revision ID: 6afabe49da38
Revises: 3cf6ea920d09
Create Date: 2019-11-05 10:55:13.208158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6afabe49da38'
down_revision = '3cf6ea920d09'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Session',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('Rating',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('recording_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('value', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['recording_id'], ['Recording.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('Recording', sa.Column('session_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'Recording', 'Session', ['session_id'], ['id'])
    op.add_column('Token', sa.Column('marked_as_bad', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('dialect', sa.String(length=255), nullable=True))
    op.add_column('user', sa.Column('pin', sa.String(length=4), nullable=True))
    op.add_column('user', sa.Column('sex', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'sex')
    op.drop_column('user', 'pin')
    op.drop_column('user', 'dialect')
    op.drop_column('user', 'age')
    op.drop_column('Token', 'marked_as_bad')
    op.drop_constraint(None, 'Recording', type_='foreignkey')
    op.drop_column('Recording', 'session_id')
    op.drop_table('Rating')
    op.drop_table('Session')
    # ### end Alembic commands ###
