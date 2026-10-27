"""adiciona localizacao e descricao em microbacias

Revision ID: b3c1d2e4f5a6
Revises: 9087658381f4
Create Date: 2026-10-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c1d2e4f5a6'
down_revision: Union[str, Sequence[str], None] = '9087658381f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # batch_alter_table: SQLite nao suporta ALTER TABLE completo
    with op.batch_alter_table('microbacias') as batch_op:
        batch_op.add_column(sa.Column('pais', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('estado', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('cidade', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('descricao', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('criado_em', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('microbacias') as batch_op:
        batch_op.drop_column('criado_em')
        batch_op.drop_column('descricao')
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
        batch_op.drop_column('cidade')
        batch_op.drop_column('estado')
        batch_op.drop_column('pais')
