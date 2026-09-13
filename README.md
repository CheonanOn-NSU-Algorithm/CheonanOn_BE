# NamJaBang_BE

남자방(NamJaBang) 서비스의 백엔드 API 서버입니다. Flask 앱 팩토리 패턴으로 구성되어 있으며, 현재는 초기 스캐폴드 단계입니다.

> **현재 상태 안내**: 이 문서는 프로젝트가 지향하는 "목표 구조"를 설명합니다. `app/models`, `app/schemas`, `app/services`, `app/api/*`는 현재 빈 패키지(`__init__.py`만 존재)이고, `app/config.py`, `app/extensions.py`, `app/errors.py`, `requirements.txt`는 아직 만들어지지 않았습니다. 아래에서 이런 항목은 **(TODO)** 로 표시했습니다. 팀원들은 이 문서를 참고해서 앞으로 이 위치에 코드를 채워나가면 됩니다.

## 1. 폴더 구조

현재 실제 폴더 구조는 다음과 같습니다.

```
.
├── README.md
├── wsgi.py                     # 앱 실행 진입점
├── static/                     # 정적 파일 (현재 비어 있음)
├── templates/                  # 템플릿 파일 (현재 비어 있음)
└── app/
    ├── __init__.py             # create_app() 앱 팩토리
    ├── api/
    │   ├── __init__.py
    │   ├── auth/
    │   │   └── __init__.py     # (TODO) routes.py 등 구현 필요
    │   ├── properties/
    │   │   └── __init__.py     # (TODO) routes.py 등 구현 필요
    │   └── regions/
    │       └── __init__.py     # (TODO) routes.py 등 구현 필요
    ├── models/
    │   └── __init__.py         # (TODO) 모델 파일 없음
    ├── schemas/
    │   └── __init__.py         # (TODO) 스키마 파일 없음
    └── services/
        └── __init__.py         # (TODO) 서비스 파일 없음
```

각 폴더/파일의 역할:

| 경로 | 역할 |
|---|---|
| `app/models/` | DB 테이블과 매핑되는 SQLAlchemy 모델 |
| `app/schemas/` | 요청/응답 데이터 형식 검증 (marshmallow) |
| `app/services/` | 실제 비즈니스 로직 (DB 조작, 외부 API 호출, 계산 등) |
| `app/api/[도메인]/` | 블루프린트 단위 라우터 (`routes.py`, `__init__.py`) |
| `app/errors.py` | 공통 에러 핸들러 — 검증 실패, 404, 500 등을 일관된 JSON 포맷으로 응답 **(TODO: 파일 없음)** |
| `app/extensions.py` | SQLAlchemy, JWT, CORS 등 확장 인스턴스 **(TODO: 파일 없음)** |
| `app/config.py` | 환경별 설정 **(TODO: 파일 없음)** |
| `wsgi.py` | 앱 실행 진입점 |

참고로 `app/__init__.py`는 현재 다음과 같이 최소 구현 상태입니다.

```python
from flask import Flask


def create_app():
    app = Flask(__name__)

    return app
```

## 2. 요청 처리 흐름

요청 하나가 처리되는 목표 흐름은 다음과 같습니다.

```
요청 도착 (app/api/<도메인>/routes.py)
        ↓
요청 형식 검증 (app/schemas/*.py, marshmallow)
        ↓
비즈니스 로직 처리 (app/services/*.py)
        ↓
DB 접근 (app/models/*.py, SQLAlchemy)
        ↓
응답 반환 (JSON)
```

검증 실패나 예외가 발생하면, `app/errors.py`에 등록될 공통 에러 핸들러가 이를 가로채 일관된 JSON 에러 포맷으로 응답하게 됩니다. (`app/errors.py`는 아직 없으므로 앞으로 만들어야 합니다.)

## 3. 새 도메인(API) 추가하는 방법

아직 완성된 도메인 예시(auth 등)가 없어서, 아래는 실제 코드가 아닌 **범용 예시 도메인 `posts`** 를 기준으로 한 제안 코드입니다. 새 도메인을 추가할 때는 이 순서와 형태를 참고하세요.

> ⚠️ 아래 코드 블록은 실제 리포지토리에 존재하는 코드가 아니라, 작성 방식을 보여주기 위한 예시 코드입니다. `db`, `ma` 등은 `app/extensions.py`에 정의될 예정이므로, 실제로 이 예시를 사용하려면 먼저 `app/extensions.py`를 만들어야 합니다.

### 3.1 `app/models/`에 모델 파일 생성

```python
# app/models/post.py (예시)
from app.extensions import db  # (TODO) app/extensions.py 작성 후 사용 가능


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
```

### 3.2 `app/schemas/`에 스키마 파일 생성

```python
# app/schemas/post_schema.py (예시)
from marshmallow import Schema, fields


class PostSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    content = fields.Str(required=True)
```

### 3.3 `app/services/`에 서비스 파일 생성

```python
# app/services/post_service.py (예시)
from app.extensions import db  # (TODO) app/extensions.py 작성 후 사용 가능
from app.models.post import Post


def create_post(data: dict) -> Post:
    post = Post(title=data["title"], content=data["content"])
    db.session.add(post)
    db.session.commit()
    return post


def get_all_posts() -> list[Post]:
    return Post.query.all()
```

### 3.4 `app/api/posts/` 폴더 생성 후 `__init__.py`, `routes.py` 작성

```python
# app/api/posts/__init__.py (예시)
from flask import Blueprint

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")

from app.api.posts import routes  # noqa: E402,F401
```

```python
# app/api/posts/routes.py (예시)
from flask import request, jsonify

from app.api.posts import posts_bp
from app.schemas.post_schema import PostSchema
from app.services.post_service import create_post, get_all_posts

post_schema = PostSchema()
posts_schema = PostSchema(many=True)


@posts_bp.route("", methods=["GET"])
def list_posts():
    posts = get_all_posts()
    return jsonify(posts_schema.dump(posts))


@posts_bp.route("", methods=["POST"])
def add_post():
    data = post_schema.load(request.get_json())
    post = create_post(data)
    return jsonify(post_schema.dump(post)), 201
```

### 3.5 `app/__init__.py`의 `create_app()`에 블루프린트 등록

현재 `create_app()`은 아래와 같이 블루프린트를 등록하지 않은 상태입니다.

```python
# app/__init__.py (현재)
from flask import Flask


def create_app():
    app = Flask(__name__)

    return app
```

새 도메인을 추가했다면, 아래처럼 블루프린트 등록 코드를 추가합니다.

```python
# app/__init__.py (예시 — 추가 후)
from flask import Flask


def create_app():
    app = Flask(__name__)

    from app.api.posts import posts_bp
    app.register_blueprint(posts_bp)

    return app
```

## 4. 실행 방법

0. 파이썬 버전 맞추기 (팀원마다 로컬 파이썬 버전이 다를 수 있어요)

   이 프로젝트는 `.python-version` 파일로 파이썬 `3.14.7`(최신 안정 버전)을 사용하도록 고정되어 있습니다.
   [pyenv](https://github.com/pyenv/pyenv) (Windows는 [pyenv-win](https://github.com/pyenv-win/pyenv-win))를 사용하면 프로젝트 디렉토리에 들어올 때 자동으로 해당 버전이 선택됩니다.
   ```bash
   pyenv install 3.14.7   # 아직 설치 안 했다면
   pyenv version           # 3.14.7 이 선택됐는지 확인
   ```

1. 가상환경 생성 및 활성화
   ```bash
   python -m venv venv
   source venv/bin/activate      # macOS/Linux
   venv\Scripts\activate         # Windows
   ```
2. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
   > **(TODO)** `requirements.txt`가 아직 없습니다. 패키지를 설치했다면 `pip freeze > requirements.txt`로 생성해서 커밋해주세요.
3. 앱 실행
   ```bash
   python wsgi.py
   ```
4. 접속 주소: `http://127.0.0.1:5000` (`wsgi.py`에서 `app.run(debug=True)`로 실행하며, 호스트/포트를 별도 지정하지 않아 Flask 기본값을 사용합니다.)

## 5. Git 브랜치 전략

- **`main`**: 항상 배포 가능한 안정 버전만 유지합니다. `develop`에서 통합 테스트를 통과한 뒤 팀장이 직접 merge합니다.
- **`develop`**: 팀원들의 작업이 모이는 통합 브랜치입니다. 모든 `feature/*` 브랜치는 여기서 분기하고, 여기로 merge됩니다.
- **`feature/도메인명`** (예: `feature/auth`, `feature/posts`): 각자 담당 도메인 작업용 브랜치입니다. `develop`에서 분기해서 생성합니다.

### 작업 순서

1. `develop` 브랜치에서 최신 상태로 pull
2. `git checkout -b feature/도메인명` (`develop` 기준으로 분기)
3. 해당 도메인 작업 진행
4. 작업 완료 후 `git add`, `commit`, `push`
5. GitHub에서 `feature/도메인명` → `develop`으로 Pull Request 생성
6. 코드 리뷰 후 `develop`으로 merge
7. `develop`에서 통합 테스트 통과 확인되면, 팀장이 `develop` → `main`으로 merge (배포 시점)

### 주의사항

- `feature` 브랜치를 `main`에서 분기하지 않도록 주의합니다 (반드시 `develop`에서 분기).
- `main`으로의 병합은 팀장만 진행합니다.

## 6. 담당자 매핑

| 도메인 | 설명 | 담당자 |
|---|---|---|
| auth | 인증/인가 | |
| properties | (예정) | |
| regions | (예정) | |

> 담당자와 도메인 설명은 팀에서 논의 후 채워주세요.
