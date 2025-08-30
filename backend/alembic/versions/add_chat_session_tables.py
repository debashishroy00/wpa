"""add_chat_session_tables

Revision ID: add_chat_session_tables
Revises: 6ab6b908bdb7
Create Date: 2025-08-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_chat_session_tables'
down_revision = '6ab6b908bdb7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('conversation_history', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('session_summary', sa.Text(), nullable=True),
        sa.Column('last_intent', sa.String(length=50), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_id'), 'chat_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_session_id'), 'chat_sessions', ['session_id'], unique=True)

    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent_detected', sa.String(length=50), nullable=True),
        sa.Column('context_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.String(length=50), nullable=True),
        sa.Column('provider', sa.String(length=20), nullable=True),
        sa.Column('temperature', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_user_id'), 'chat_messages', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop chat_messages table
    op.drop_index(op.f('ix_chat_messages_user_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_session_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
    
    # Drop chat_sessions table
    op.drop_index(op.f('ix_chat_sessions_session_id'), table_name='chat_sessions')
    op.drop_index(op.f('ix_chat_sessions_user_id'), table_name='chat_sessions')
    op.drop_index(op.f('ix_chat_sessions_id'), table_name='chat_sessions')
    op.drop_table('chat_sessions')