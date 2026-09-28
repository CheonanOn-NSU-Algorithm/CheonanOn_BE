from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.schemas.bookmark import (
    BookmarkCreateSchema,
    BookmarkResponseSchema,
    BookmarkListResponseSchema,
)
from app.services.bookmark_service import BookmarkService


bookmark_bp = Blueprint(
    "bookmarks",
    __name__,
    url_prefix="/api/v1/bookmarks",
)


@bookmark_bp.get("")
@jwt_required()
def get_bookmarks():
    user_id = get_jwt_identity()

    result = BookmarkService.get_bookmarks(user_id)

    return jsonify(
        BookmarkListResponseSchema().dump(result)
    ), 200


@bookmark_bp.post("")
@jwt_required()
def create_bookmark():
    try:
        data = BookmarkCreateSchema().load(
            request.get_json()
        )
    except ValidationError as e:
        return jsonify({
            "success": False,
            "message": "잘못된 요청입니다.",
            "errors": e.messages,
        }), 400

    user_id = get_jwt_identity()
    event_id = data["eventId"]

    result = BookmarkService.create_bookmark(
        user_id,
        event_id,
    )

    if result is None:
        return jsonify({
            "success": False,
            "message": "존재하지 않는 행사입니다.",
        }), 404

    return jsonify(
        BookmarkResponseSchema().dump(result)
    ), 201


@bookmark_bp.delete("/<int:event_id>")
@jwt_required()
def delete_bookmark(event_id):
    user_id = get_jwt_identity()

    result = BookmarkService.delete_bookmark(
        user_id,
        event_id,
    )

    return jsonify(
        BookmarkResponseSchema().dump(result)
    ), 200