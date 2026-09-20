# CheonanOn_BE

## 1. 실행 방법

0. 파이썬 버전 맞추기 (팀원마다 로컬 파이썬 버전이 다를 수 있어요)
   ```
   파이썬 org 홈페이지에서 3.14.7 릴리스 자기 OS 환경에 맞추어 다운로드
   ```
1. 가상환경 생성 및 활성화
   ```
   git 으로 파일 받아온 후
   파이참 아래 인터프리터설정
   새 인터프리터 추가 로컬 인터프리터 추가 누르기
   새로 만들기 누르고 파이썬 3.14누르기
   이후 터미널에서 파이썬 버전 확인 3.14.7 나와야함
   python --version
   ```
2. 의존성 설치
   ```bash
   # 새로 의존성 설치할 때마다 requirements.txt 생성
   pip freeze > requirements.txt

   # 클론 후 의존성 받아올 때 
   pip install -r requirements.txt
   ```
3. 앱 실행
   ```bash
   python wsgi.py
   ```
4. 접속 주소: `http://127.0.0.1:5000` (`wsgi.py`에서 `app.run(debug=True)`로 실행하며, 호스트/포트를 별도 지정하지 않아 Flask 기본값을 사용합니다.)

## 2. Git 브랜치 전략

- **`main`**: 항상 배포 가능한 안정 버전만 유지합니다. `develop`에서 통합 테스트를 통과한 뒤 팀장이 직접 merge합니다.
- **`develop`**: 팀원들의 작업이 모이는 통합 브랜치입니다. 모든 `feature/*` 브랜치는 여기서 분기하고, 여기로 merge됩니다.
- **`feature/도메인명-이름`** (예: `feature/auth-MinYeong`, `feature/posts-Chulsoo`): 각자 담당 도메인 작업용 브랜치입니다. `develop`에서 분기해서 생성합니다. 같은 도메인을 여러 명이 나눠 맡을 수 있으니 브랜치 이름 끝에 본인 이름을 붙입니다.

### 작업 순서

1. `develop` 브랜치에서 최신 상태로 pull
2. `git checkout -b feature/도메인명-이름` (`develop` 기준으로 분기)
3. 해당 도메인 작업 진행
4. 작업 완료 후 `git add`, `commit`, `push`
5. GitHub에서 `feature/도메인명` → `develop`으로 Pull Request 생성
6. 코드 리뷰 후 `develop`으로 merge
7. `develop`에서 통합 테스트 통과 확인되면, 팀장이 `develop` → `main`으로 merge (배포 시점)

### 주의사항

- `feature` 브랜치를 `main`에서 분기하지 않도록 주의합니다 (반드시 `develop`에서 분기).
- `main`으로의 병합은 팀장만 진행합니다.

## 3. 커밋 컨벤션

커밋 메시지는 `타입: 내용` 형식으로 작성합니다.

```
feat: 카카오 로그인 API 추가
fix: 토큰 만료 시간 계산 오류 수정
docs: README 실행 방법 보강
refactor: 에러 클래스 구조 정리
```

| 타입 | 의미 |
|---|---|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 (README, 주석 등) |
| `refactor` | 기능 변경 없는 코드 구조 개선 |
| `test` | 테스트 코드 추가/수정 |
| `chore` | 빌드/설정/의존성 등 기타 작업 |

- 제목은 한 줄로 간결하게, 마침표는 붙이지 않습니다.
- 여러 작업을 한 커밋에 몰아넣지 말고, 의미 단위로 쪼개서 커밋합니다.

## 4. DB 마이그레이션 (Flask-Migrate)

DB 스키마(테이블/컬럼) 변경은 `db.create_all()`처럼 자동으로 맞추지 않고, **Flask-Migrate(Alembic)**로 버전 관리합니다. 모델을 바꿀 때마다 변경 이력이 담긴 스크립트 파일을 만들어 git으로 공유하기 때문에, 팀원 전체가 같은 명령으로 로컬 DB를 동일한 스키마 상태로 맞출 수 있습니다.

### 최초 1회 설정

Flask CLI가 앱을 찾을 수 있도록 터미널에서 환경변수를 지정합니다 (`wsgi.py`에 `app = create_app()`이 있어 자동 인식됩니다).

```bash
export FLASK_APP=wsgi.py
```

### 새로 clone 했거나 pull 받은 뒤 (테이블 생성/갱신)

```bash
flask db upgrade
```

`migrations/versions/` 안의 스크립트들을 순서대로 적용해서 로컬 MySQL DB를 최신 스키마로 맞춰줍니다. 모델을 직접 만들거나 수정할 필요 없이 이 명령 한 줄이면 됩니다.

### 모델을 새로 추가하거나 수정했을 때

```bash
# 1. 모델 변경 후, 변경사항을 비교해서 마이그레이션 스크립트 생성
flask db migrate -m "feat: user 테이블에 nickname 컬럼 추가"

# 2. migrations/versions/ 에 생성된 스크립트를 열어서 의도한 대로 만들어졌는지 확인
#    (자동 생성이 완벽하지 않을 수 있어 리뷰 필수)

# 3. 실제 DB에 반영
flask db upgrade
```

- `-m` 뒤의 마이그레이션 메시지도 **커밋 컨벤션과 동일한 타입 접두어**(`feat`, `fix`, `refactor` 등)를 붙여서 작성합니다. 나중에 `migrations/versions/`만 훑어봐도 어떤 변경이 어떤 의도였는지 알 수 있게 하기 위함입니다.
- 모델 파일과 그 모델로 생성된 마이그레이션 스크립트(`migrations/versions/*.py`)는 **같은 커밋에 함께 포함**합니다. 스크립트 없이 모델만 커밋하면 다른 팀원은 `flask db upgrade`를 해도 테이블이 생기지 않습니다.
- `migrations/` 폴더 전체(`alembic.ini`, `env.py`, `script.py.mako`, `versions/`)는 git으로 관리되는 프로젝트 파일입니다. `.gitignore`에 추가하지 마세요.
