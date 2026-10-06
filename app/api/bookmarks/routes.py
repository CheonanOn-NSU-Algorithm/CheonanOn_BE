from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.common_response import CommonResponse
from app.schemas.bookmark import (
    BookmarkActionApiResponseSchema,
    BookmarkCreateSchema,
    BookmarkListApiResponseSchema,
)
from app.services.bookmark_service import add_bookmark, get_my_bookmarks, remove_bookmark
from .blueprint import bookmark_bp


@bookmark_bp.route("", methods=["POST"])
@jwt_required()
def create():
    """로그인한 사용자의 북마크를 추가한다 (새 항목은 201, 기존 항목은 200)."""
    user_id = int(get_jwt_identity())
    # 요청 본문을 스키마로 검증한 뒤 두 입력 표기 중 전달된 행사 ID를 사용한다.
    data = BookmarkCreateSchema().load(request.get_json(silent=True) or {})
    event_id = data.get("eventId", data.get("event_id"))
    _, created = add_bookmark(user_id, event_id)
    response = BookmarkActionApiResponseSchema().dump(
        CommonResponse.success({"eventId": event_id, "isBookmarked": True})
    )
    return jsonify(response), 201 if created else 200


@bookmark_bp.route("", methods=["GET"])
@bookmark_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my():
    """로그인한 사용자 본인의 북마크 목록만 반환한다."""
    user_id = int(get_jwt_identity())
    bookmarks = get_my_bookmarks(user_id)
    response = BookmarkListApiResponseSchema().dump(CommonResponse.success(bookmarks))
    return jsonify(response), 200


@bookmark_bp.route("/<int:event_id>", methods=["DELETE"])
@jwt_required()
def delete(event_id):
    """로그인한 사용자의 특정 행사 북마크를 해제한다."""
    user_id = int(get_jwt_identity())
    result = remove_bookmark(user_id, event_id)
    response = BookmarkActionApiResponseSchema().dump(
        CommonResponse.success(result)
    )
    return jsonify(response), 200
