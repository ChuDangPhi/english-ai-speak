"""add_email_verification_fields_only

Revision ID: 1d1af29f4177
Revises: 
Create Date: 2026-01-15 12:04:54.448557

Migration đơn giản chỉ thêm 5 columns cho email verification và password reset.
Không thay đổi index hay các bảng khác.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1d1af29f4177'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Thêm 5 columns mới vào bảng users cho:
    - Email verification (3 columns)
    - Password reset (2 columns)
    """
    # Email verification columns
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('email_verification_sent_at', sa.DateTime(), nullable=True))
    
    # Password reset columns
    op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_reset_token_expires_at', sa.DateTime(), nullable=True))
    
    # Create indexes for token lookups (fast search by token)
    op.create_index('ix_users_email_verification_token', 'users', ['email_verification_token'])
    op.create_index('ix_users_password_reset_token', 'users', ['password_reset_token'])


def downgrade() -> None:
    """
    Rollback: Xóa 5 columns đã thêm
    """
    # Drop indexes first
    op.drop_index('ix_users_password_reset_token', table_name='users')
    op.drop_index('ix_users_email_verification_token', table_name='users')
    
    # Drop columns
    op.drop_column('users', 'password_reset_token_expires_at')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'email_verification_sent_at')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
