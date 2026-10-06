from flask import Blueprint

bookmark_bp = Blueprint("bookmarks", __name__, url_prefix="/bookmarks")

from . import routes  # noqa: E402,F401
