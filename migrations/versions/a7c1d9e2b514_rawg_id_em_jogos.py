"""rawg_id em jogos

Associa cada jogo local ao registro correspondente da RAWG. A coluna é
nula para todos os jogos já cadastrados: nenhum dado existente é
alterado, e as imagens (`capa_url`, `arquivo_capa`) ficam como estão.

Revision ID: a7c1d9e2b514
Revises: e3284488f586
Create Date: 2026-10-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7c1d9e2b514'
down_revision = 'e3284488f586'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('jogos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rawg_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_jogos_rawg_id'), ['rawg_id'], unique=True)


def downgrade():
    with op.batch_alter_table('jogos', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_jogos_rawg_id'))
        batch_op.drop_column('rawg_id')
