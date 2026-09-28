import os                      # .env/환경변수 값을 읽어오기 위한 표준 라이브러리
import re
from datetime import timedelta # JWT 토큰 만료 기간을 지정하기 위해 사용

from dotenv import load_dotenv # .env 파일을 파싱해서 os.environ에 로드해주는 라이브러리
from sqlalchemy.engine import make_url

# .env 파일 내용을 읽어서 os.environ에 등록하는 함수
load_dotenv()


def database_uri():
    # DB 접속 정보는 기존 URI에서 읽고, 선택적인 DB 이름 재지정만 별도로 적용한다.
    uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
    database_name = os.environ.get("CHEONANON_DB_NAME")
    if not uri or not database_name:
        return uri
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", database_name):
        # URL이나 SQL 구문을 DB 이름으로 받아 접속 대상이 뜻밖에 바뀌지 않게 제한한다.
        raise ValueError("CHEONANON_DB_NAME must be a simple database name")
    return make_url(uri).set(database=database_name).render_as_string(hide_password=False)


class Config:
    # JWT 서명/검증에 쓰는 비밀키. .env의 JWT_SECRET_KEY 값을 그대로 사용
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

    # 한국관광공사 API 키. .env의 TOURAPI_KEY 값을 그대로 사용
    TOURAPI_KEY = os.environ.get("TOURAPI_KEY")

    # access token 유효기간 (짧게 유지, 만료되면 refresh token으로 재발급)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # refresh token 유효기간 (access token보다 길게)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)

    # DB 접속 URL. CHEONANON_DB_NAME이 있으면 기존 접속 정보에서 DB 이름만 교체
    SQLALCHEMY_DATABASE_URI = database_uri()
