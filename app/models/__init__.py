# models 패키지의 진입점(entrypoint).
# 회원 모델 User는 user.py에, 축제와 관련 테이블은 event.py에 정의되어 있다.
# 기존 관광 정보 모델은 tour_content.py에, 토큰 차단 모델은 token_blocklist.py에 있다.
# 이 파일에서 각 모델을 모아 import하면 다른 코드에서는
#   from app.models import User, Event, TokenBlocklist
# 처럼 실제 정의 파일의 위치를 몰라도 필요한 모델을 가져올 수 있다.
#
# Flask-Migrate(Alembic)의 마이그레이션 자동 생성은 현재 import된 db.Model 클래스와
# DB 스키마를 비교한다. 모델 파일이 import되지 않으면 테이블 정의를 발견하지 못한다.
# app/__init__.py의 `from app import models`가 이 파일을 실행하므로,
# 앱을 시작할 때 아래 모델들이 모두 등록된다.
#
# __all__은 `from app.models import *`에서 공개할 이름을 명시한다.

from app.models.token_blocklist import TokenBlocklist
from app.models.tour_content import TourContent, PlaceDetail, FestivalDetail
from app.models.event import (Category, Sido, Event, Tag, EventTag,
                              EventDailyView, Review, ReviewImage, Bookmark)
from app.models.user import User

__all__ = ["User", "TokenBlocklist", "TourContent", "PlaceDetail", "FestivalDetail",
           "Category", "Sido", "Event", "Tag", "EventTag",
           "EventDailyView", "Review", "ReviewImage", "Bookmark"]
