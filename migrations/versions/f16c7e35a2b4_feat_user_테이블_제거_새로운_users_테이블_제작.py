"""빈 레거시 user 테이블 제거; 회원 정보는 users에만 저장한다.

Revision ID: f16c7e35a2b4
Revises: c2b0d920b672
"""

from alembic import op
import sqlalchemy as sa

revision = "f16c7e35a2b4"
down_revision = "c2b0d920b672"
branch_labels = None
depends_on = None


def upgrade():
    # 이전 리비전의 단수형 user는 새 users와 별개다. 데이터가 있으면 삭제하지 않고 중단한다.
    if sa.inspect(op.get_bind()).has_table("user"):
        count = op.get_bind().scalar(sa.text("SELECT COUNT(*) FROM user"))
        if count:
            raise RuntimeError("기존 user 테이블에 데이터가 있어 자동 삭제하지 않습니다.")
        op.drop_table("user")


def downgrade():
    # 롤백할 때는 이전 스키마의 빈 user 테이블 구조만 복원한다.
    op.create_table("user",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("kakao_id", sa.BigInteger, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=False),
        sa.Column("profile_image", sa.String(500)),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False))
    op.create_index("ix_user_kakao_id", "user", ["kakao_id"], unique=True)
    op.create_index("ix_user_email", "user", ["email"], unique=True)
