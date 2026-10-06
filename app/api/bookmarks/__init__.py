"""북마크 Blueprint를 외부에 공개하고 라우트를 등록한다."""

from .blueprint import bookmark_bp

# 패키지를 import할 때 라우트 데코레이터를 실행해 URL을 Blueprint에 등록한다.
from . import routes  # noqa: E402,F401
