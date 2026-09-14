import os
from datetime import timedelta

from dotenv import load_dotenv

# .env 파일 내용을 읽어서 os.environ에 등록하는 함수
load_dotenv()


class Config:
    # JWT 서명/검증에 쓰는 비밀키. .env의 JWT_SECRET_KEY 값을 그대로 사용
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

    # access token 유효기간 (짧게 유지, 만료되면 refresh token으로 재발급)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # refresh token 유효기간 (access token보다 길게)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)

    # DB 접속 URL. .env의 SQLALCHEMY_DATABASE_URI 값을 그대로 사용
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
