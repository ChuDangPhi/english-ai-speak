"""add phone and bio columns to users table

Revision ID: add_phone_bio_001
Revises: 1d1af29f4177
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_phone_bio_001'
down_revision: Union[str, None] = '1d1af29f4177'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add phone and bio columns to users table"""
    # Add phone column
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    
    # Add bio column
    op.add_column('users', sa.Column('bio', sa.String(500), nullable=True))


def downgrade() -> None:
    """Remove phone and bio columns from users table"""
    op.drop_column('users', 'bio')
    op.drop_column('users', 'phone')
