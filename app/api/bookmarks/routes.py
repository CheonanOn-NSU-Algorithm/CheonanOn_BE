from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.common_response import CommonResponse
from app.schemas.bookmark import (
    BookmarkCreateSchema,
    BookmarkListResponseSchema,
    BookmarkResponseSchema,
)
from app.services.bookmark_service import add_bookmark, get_my_bookmarks, remove_bookmark
from . import bookmark_bp


@bookmark_bp.route("", methods=["POST"])
@jwt_required()
def create():
    user_id = int(get_jwt_identity())
    data = BookmarkCreateSchema().load(request.get_json(silent=True) or {})
    event_id = data.get("eventId", data.get("event_id"))
    _, created = add_bookmark(user_id, event_id)
    response = BookmarkResponseSchema().dump(
        {"eventId": event_id, "isBookmarked": True}
    )
    return jsonify(CommonResponse.success(response)), 201 if created else 200


@bookmark_bp.route("", methods=["GET"])
@bookmark_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my():
    user_id = int(get_jwt_identity())
    bookmarks = get_my_bookmarks(user_id)
    result = BookmarkListResponseSchema().dump(bookmarks)
    return jsonify(CommonResponse.success(result)), 200


@bookmark_bp.route("/<int:event_id>", methods=["DELETE"])
@jwt_required()
def delete(event_id):
    user_id = int(get_jwt_identity())
    result = remove_bookmark(user_id, event_id)
    return jsonify(CommonResponse.success(BookmarkResponseSchema().dump(result))), 200
