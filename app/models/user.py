# 카카오로 로그인한 회원 정보는 여기서 다룬다.
# 클래스 이름은 User지만 실제 테이블 이름은 아래 __tablename__에 적힌 users다.
# 예전 user 테이블을 다시 만드는 건 아니다.

# db.Column으로 테이블의 컬럼을 정의할 때 쓰는 객체다.
from app.extensions import db

# 행사 테이블과 회원 테이블의 ID 타입, 시간 기록 방식을 맞추려고 같이 쓴다.
from app.models.event import BIGINT_PK, utc_now


class User(db.Model):
    # db.Model을 상속해야 SQLAlchemy가 이 클래스를 테이블로 알아본다.
    __tablename__ = "users"

    # 우리 서비스에서 회원을 구분할 때 쓰는 ID다. 리뷰나 북마크도 이 ID로 회원을 찾는다.
    # 카카오 ID와는 다른 값이다. MySQL에서는 BIGINT, SQLite에서는 INTEGER를 쓴다.
    id = db.Column(BIGINT_PK, primary_key=True, autoincrement=True)

    # 카카오에서 받은 회원 식별자다. 예전 모델에선 숫자였지만 지금은 문자열로 저장한다.
    # 로그인할 때 이 값으로 기존 회원을 찾는다. 중복 방지 설정은 파일 맨 아래에 있다.
    kakao_id = db.Column(db.String(64), nullable=False)

    # 닉네임은 꼭 있어야 한다. 이메일과 프로필 이미지는 카카오에서 안 줄 수도 있어서 비워둘 수 있다.
    # 예전과 달리 이메일이 없어도 되고, 같은 이메일이 다른 행에 들어갈 수도 있다.
    nickname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255))
    profile_image_url = db.Column(db.String(500))

    # 가입할 때 약관과 개인정보 처리에 동의한 시각이다. 두 값 모두 있어야 저장된다.
    # 여기서는 칸만 정의한다. 동의받고 시각을 넣는 일은 로그인·가입 코드에서 해야 한다.
    terms_agreed_at = db.Column(db.DateTime, nullable=False)
    privacy_agreed_at = db.Column(db.DateTime, nullable=False)

    # 마지막으로 로그인한 시각이다. 자동으로 바뀌지는 않으니 로그인할 때 갱신해야 한다.
    last_login_at = db.Column(db.DateTime)

    # 회원을 처음 저장하면 생성·수정 시각이 함께 들어간다. 이후 수정하면 updated_at만 바뀐다.
    # 이 동작은 SQLAlchemy로 저장할 때 적용된다. DB에 직접 SQL을 실행할 땐 따로 넣어야 한다.
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # 같은 카카오 계정으로 회원이 두 번 만들어지지 않게 DB에서도 막는다.
    __table_args__ = (db.UniqueConstraint("kakao_id", name="uq_users_kakao_id"),)
