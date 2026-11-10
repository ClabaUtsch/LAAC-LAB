"""comunidade social progressao avatar amizades compra

Revision ID: b8e4f1a2c903
Revises: e3284488f586
Create Date: 2026-11-10
"""
from alembic import op
import sqlalchemy as sa

revision = "b8e4f1a2c903"
down_revision = "a7c1d9e2b514"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("usuarios") as batch:
        batch.add_column(sa.Column("cpf", sa.String(length=11), nullable=True))
        batch.add_column(sa.Column("ultimo_dia_ativo", sa.Date(), nullable=True))
        batch.add_column(sa.Column("aceite_termos_em", sa.DateTime(), nullable=True))
        batch.add_column(
            sa.Column(
                "email_verificado",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.create_unique_constraint("uq_usuarios_cpf", ["cpf"])

    with op.batch_alter_table("badges") as batch:
        batch.add_column(sa.Column("codigo", sa.String(length=40), nullable=True))
        batch.create_unique_constraint("uq_badges_codigo", ["codigo"])

    with op.batch_alter_table("posts") as batch:
        batch.add_column(sa.Column("parent_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_posts_parent_id", "posts", ["parent_id"], ["id"], ondelete="CASCADE"
        )

    with op.batch_alter_table("jogos") as batch:
        batch.add_column(sa.Column("links_compra", sa.JSON(), nullable=True))

    op.create_table(
        "amizades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("solicitante_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destinatario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pendente"),
        sa.Column("criado_em", sa.DateTime(), nullable=True),
        sa.Column("respondido_em", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("solicitante_id", "destinatario_id"),
    )

    op.create_table(
        "membros_comunidade",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jogo_id", sa.Integer(), sa.ForeignKey("jogos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entrou_em", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("usuario_id", "jogo_id"),
    )

    op.create_table(
        "recuperacoes_senha",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("expira_em", sa.DateTime(), nullable=False),
        sa.Column("usado_em", sa.DateTime(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("recuperacoes_senha")
    op.drop_table("membros_comunidade")
    op.drop_table("amizades")
    with op.batch_alter_table("jogos") as batch:
        batch.drop_column("links_compra")
    with op.batch_alter_table("posts") as batch:
        batch.drop_constraint("fk_posts_parent_id", type_="foreignkey")
        batch.drop_column("parent_id")
    with op.batch_alter_table("badges") as batch:
        batch.drop_constraint("uq_badges_codigo", type_="unique")
        batch.drop_column("codigo")
    with op.batch_alter_table("usuarios") as batch:
        batch.drop_constraint("uq_usuarios_cpf", type_="unique")
        batch.drop_column("email_verificado")
        batch.drop_column("aceite_termos_em")
        batch.drop_column("ultimo_dia_ativo")
        batch.drop_column("cpf")
