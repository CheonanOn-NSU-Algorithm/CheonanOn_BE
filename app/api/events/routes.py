# 행사 HTTP 엔드포인트. 요청 검증은 스키마, 검색과 DB 조회는 서비스가 담당한다.
# 이 파일은 요청값 전달과 공통 JSON 응답 생성만 수행한다.

from flask import Blueprint, jsonify, request

from app.common_response import CommonResponse
from app.schemas.events import (
    CategoryOptionSchema,
    EmptyQuerySchema,
    EventDetailSchema,
    EventPathSchema,
    EventListQuerySchema,
    EventListResponseSchema,
    MonthlyTopQuerySchema,
    MonthlyTopResponseSchema,
    SidoOptionSchema,
)
from app.services.event_service import EventService


# 앱 팩토리에서 /api/v1/event를 붙인다. 여기에는 행사별 경로만 정의한다.
events_bp = Blueprint("events", __name__)


@events_bp.get("/categories")
def list_categories():
    # 입력값 없는 선택지 조회. 잘못 붙인 쿼리는 스키마에서 거부한다.
    EmptyQuerySchema().load(request.args)
    categories = EventService.list_categories()
    data = CategoryOptionSchema(many=True).dump(categories)
    return jsonify(CommonResponse.success(data)), 200


@events_bp.get("/sidos")
def list_sidos():
    # 받은 code는 프론트에서 선택한 뒤 행사 목록 요청의 sido_code로 전달한다.
    EmptyQuerySchema().load(request.args)
    sidos = EventService.list_sidos()
    data = SidoOptionSchema(many=True).dump(sidos)
    return jsonify(CommonResponse.success(data)), 200


@events_bp.get("")
def list_events():
    # 쿼리 파라미터의 타입·범위를 스키마에서 검사한 뒤 서비스에 전달한다.
    query = EventListQuerySchema().load(request.args)
    result = EventService.list_events(query)
    data = EventListResponseSchema().dump(result)
    return jsonify(CommonResponse.success(data)), 200


@events_bp.get("/monthly-top")
def monthly_top_events():
    # 조회할 월과 카드 개수를 검증한다. 월 경계와 순위 계산은 서비스에서 맡는다.
    query = MonthlyTopQuerySchema().load(request.args)
    result = EventService.monthly_top(query)
    data = MonthlyTopResponseSchema().dump(result)
    return jsonify(CommonResponse.success(data)), 200


@events_bp.get("/<int:event_id>")
def get_event(event_id):
    # 경로의 정수 ID로 행사를 조회하고 서비스에서 조회수를 기록한다.
    EmptyQuerySchema().load(request.args)
    params = EventPathSchema().load({"event_id": event_id})
    event = EventService.get_event(params["event_id"], request_method=request.method)
    data = EventDetailSchema().dump(event)
    return jsonify(CommonResponse.success(data)), 200
