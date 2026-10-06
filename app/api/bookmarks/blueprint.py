"""북마크 API 라우트가 공유하는 Blueprint 객체."""

from flask import Blueprint


bookmark_bp = Blueprint("bookmarks", __name__, url_prefix="/bookmarks")
