# 행사 HTTP 엔드포인트. 요청 검증은 스키마, 검색과 DB 조회는 서비스가 담당한다.
# 이 파일은 요청값 전달과 공통 JSON 응답 생성만 수행한다.

from flask import Blueprint, jsonify, request

from app.common_response import CommonResponse
from app.schemas.events import (
    EventDetailSchema,
    EventListQuerySchema,
    EventListResponseSchema,
)
from app.services.event_service import EventService


# 앱 팩토리에서 /api/v1/event를 붙인다. 여기에는 행사별 경로만 정의한다.
events_bp = Blueprint("events", __name__)


@events_bp.get("")
def list_events():
    # 쿼리 파라미터의 타입·범위를 스키마에서 검사한 뒤 서비스에 전달한다.
    query = EventListQuerySchema().load(request.args.to_dict())
    result = EventService.list_events(query)
    data = EventListResponseSchema().dump(result)
    return jsonify(CommonResponse.success(data)), 200


@events_bp.get("/<int:event_id>")
def get_event(event_id):
    # 경로의 정수 ID로 행사 한 건을 가져와 상세 화면용 필드만 반환한다.
    event = EventService.get_event(event_id)
    data = EventDetailSchema().dump(event)
    return jsonify(CommonResponse.success(data)), 200
