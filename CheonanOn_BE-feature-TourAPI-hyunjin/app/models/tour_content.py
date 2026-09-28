# TourAPI 데이터를 저장할 테이블
from datetime import datetime, timezone

from app.extensions import db


def utc_now():
    # 시간은 UTC로 통일. MySQL DATETIME에 넣을 때는 시간대 정보만 제거
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    # 세 테이블에서 같이 쓰는 생성일, 수정일

    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class TourContent(TimestampMixin, db.Model):
    # 관광지, 문화시설, 축제 공통 정보. content_id가 같으면 같은 콘텐츠

    __tablename__ = "tour_content"

    id = db.Column(db.Integer, primary_key=True)

    # API 콘텐츠 ID와 타입 (12: 관광지, 14: 문화시설, 15: 축제)
    content_id = db.Column(db.String(30), nullable=False, index=True, unique=True)
    content_type_id = db.Column(db.SmallInteger, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)

    # 주소와 연락처
    addr1 = db.Column(db.String(255), nullable=True)
    addr2 = db.Column(db.String(255), nullable=True)
    zipcode = db.Column(db.String(20), nullable=True)
    tel = db.Column(db.String(100), nullable=True)
    homepage = db.Column(db.Text, nullable=True)
    overview = db.Column(db.Text, nullable=True)

    # 이미지와 좌표: map_x는 경도, map_y는 위도
    first_image = db.Column(db.String(500), nullable=True)
    first_image2 = db.Column(db.String(500), nullable=True)
    map_x = db.Column(db.Numeric(13, 10), nullable=True)
    map_y = db.Column(db.Numeric(12, 10), nullable=True)
    # 주소에서 가져온 지역명 (아산시, 천안시 동남구 등)
    district = db.Column(db.String(20), nullable=True, index=True)

    # API에서 수정된 시간 / 목록과 상세를 DB에 저장한 시간
    api_modified_at = db.Column(db.DateTime, nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=False)
    common_detail_synced_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "content_type_id IN (12, 14, 15)",
            name="ck_tour_content_type",
        ),
    )
    place_detail = db.relationship(
        "PlaceDetail",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    festival_detail = db.relationship(
        "FestivalDetail",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PlaceDetail(TimestampMixin, db.Model):
    # 관광지와 문화시설의 이용 안내, 체험 정보

    __tablename__ = "place_detail"

    id = db.Column(db.Integer, primary_key=True)
    # 콘텐츠 하나에 상세 하나만 연결. 공통 정보 삭제 시 상세도 같이 삭제
    tour_content_id = db.Column(
        db.Integer,
        db.ForeignKey("tour_content.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # 문의·운영 시간·요금
    info_center = db.Column(db.String(100), nullable=True)
    open_date = db.Column(db.String(100), nullable=True)
    rest_date = db.Column(db.String(255), nullable=True)
    use_time = db.Column(db.Text, nullable=True)
    use_fee = db.Column(db.Text, nullable=True)
    parking = db.Column(db.Text, nullable=True)

    # 체험 및 편의시설
    experience_guide = db.Column(db.Text, nullable=True)
    experience_age = db.Column(db.String(255), nullable=True)
    baby_carriage = db.Column(db.String(100), nullable=True)
    pet = db.Column(db.String(100), nullable=True)
    credit_card = db.Column(db.String(100), nullable=True)

    # 별도 컬럼이 없는 정보는 JSON에 모아두기
    detail_data = db.Column(db.JSON, nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=False)


class FestivalDetail(TimestampMixin, db.Model):
    # 축제 일정, 장소, 주최 정보

    __tablename__ = "festival_detail"

    id = db.Column(db.Integer, primary_key=True)
    # 콘텐츠 하나에 상세 하나만 연결. 공통 정보 삭제 시 상세도 같이 삭제
    tour_content_id = db.Column(
        db.Integer,
        db.ForeignKey("tour_content.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # 축제 날짜. 시작일이 종료일보다 늦으면 안 됨
    event_start_date = db.Column(db.Date, nullable=False, index=True)
    event_end_date = db.Column(db.Date, nullable=False, index=True)
    event_place = db.Column(db.String(255), nullable=True)
    play_time = db.Column(db.Text, nullable=True)
    use_fee = db.Column(db.Text, nullable=True)

    # 주최자(sponsor)와 주관사(organizer)
    sponsor = db.Column(db.String(255), nullable=True)
    sponsor_tel = db.Column(db.String(100), nullable=True)
    organizer = db.Column(db.String(255), nullable=True)
    organizer_tel = db.Column(db.String(100), nullable=True)
    program = db.Column(db.Text, nullable=True)

    # 별도 컬럼이 없는 정보는 JSON에 모아두기
    detail_data = db.Column(db.JSON, nullable=True)
    last_synced_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "event_start_date <= event_end_date",
            name="ck_festival_date_range",
        ),
    )
