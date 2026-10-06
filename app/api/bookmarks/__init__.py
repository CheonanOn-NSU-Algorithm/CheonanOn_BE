"""북마크 URL 접두사와 라우트를 묶는 Flask Blueprint."""

from flask import Blueprint

# 부모 API Blueprint에서 이 기능 전체를 /api/bookmarks 아래에 등록한다.
bookmark_bp = Blueprint("bookmarks", __name__, url_prefix="/bookmarks")

# Blueprint를 먼저 만든 후 routes를 import해야 같은 객체에 라우트가 연결된다.
from . import routes  # noqa: E402,F401
