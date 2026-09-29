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

## 5. TourAPI 전국 축제 데이터 저장

### 준비와 테이블

`.env`에 `TOURAPI_KEY`와 `SQLALCHEMY_DATABASE_URI`를 설정합니다. API 키는 공공데이터포털의 한국관광공사 국문 관광정보 서비스 GW 키입니다. 아래 명령은 PowerShell에서 프로젝트 루트 기준으로 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m flask --app wsgi db upgrade
.\.venv\Scripts\python.exe -m flask --app wsgi shell
```

이번 수집에서 사용하는 테이블은 `events`, `event_tags`, `tags`, `event_daily_views`, `sidos`, `categories` 여섯 개입니다. 숫자형 PK/FK는 모두 `INT`이며, `sidos.code`는 TourAPI의 두 자리 지역 코드이므로 문자형입니다. 마이그레이션이 카테고리 5개, 시도 16개, 검색 태그 사전을 채웁니다. 이전 개발용 `tour_content`, `place_detail`, `festival_detail` 테이블은 새 초기화 스키마에서 생성하지 않습니다. 기존 개발 DB를 초기화하면 이전 데이터는 삭제되며 전국 축제를 다시 수집해야 합니다.

### 수집 실행

```python
from app.services.tour_sync import TourSyncService

service = TourSyncService()
result = service.sync_festivals("20260101", "20261231")  # 전국 축제·공연·전시 등 행사
print(result)

# 기간을 생략하면 실행 시점의 1월 1일부터 12월 31일까지 조회합니다.
result = service.sync_festivals()

# 이미 events에 저장된 행사 한 건의 상세 정보만 다시 가져옵니다.
event_id = service.sync_detail("2746930")  # TourAPI contentid; 실제 저장된 ID로 변경
```

`sync_festivals()`는 `searchFestival2`를 지역 필터 없이 조회하므로 전국 범위입니다. 한 페이지에 100건씩 `totalCount`까지 조회합니다. 시작일과 종료일은 둘 다 `YYYYMMDD` 형식으로 전달하거나 둘 다 생략해야 합니다. `TourAPI.festival()`은 DB 저장 없이 목록만 확인할 때 사용할 수 있습니다.

각 목록 항목마다 `detailCommon2`와 `detailIntro2`를 가져온 뒤 `tour_content_id`를 기준으로 `events`에 추가 또는 갱신합니다. 상세 API 호출과 검증이 모두 끝나기 전에는 DB를 바꾸지 않습니다. `overview`는 소개글, `eventplace`는 장소, `mapy`/`mapx`는 위도/경도, `lDongRegnCd` 앞 두 자리는 `sidos.code`에 대응합니다. `lclsSystm3`은 시드 분류 규칙에 따라 축제·계절행사·공연·전시·체험으로 변환합니다. 소개글에서 시드 태그 단어가 발견되면 `event_tags`를 갱신합니다. `fee_text`는 실제 API 응답이 500자를 넘을 수 있어 원문을 `TEXT`로 저장합니다. 요금은 명확한 원 단위 금액이나 무료 표시가 있을 때만 `price`와 `is_free`로 변환하고, 판단할 수 없으면 `NULL`로 둡니다.

응답에 아예 없는 필드는 기존 값을 유지합니다. 같은 ID를 다시 수집해도 새 행사 행이 중복 생성되지 않으며 `view_count`와 `event_daily_views` 값도 초기화하지 않습니다. 조회수 증가는 행사 상세 API 구현에서 처리해야 하며 이 수집 서비스는 조회수를 증가시키지 않습니다. 행사 기간이 90일을 넘으면 `is_permanent`가 참이 됩니다.

반환값은 `{"saved": 0, "failures": [], "complete": True}` 형태입니다. `saved`는 저장 성공 항목 수, `failures`는 페이지·content ID·에러 코드·메시지, `complete`는 실패가 하나도 없었는지를 뜻합니다. 한 축제 저장이 실패하면 해당 축제 트랜잭션만 롤백하고 다음 항목을 계속합니다. 목록 페이지 자체가 실패하면 그 시점에 중단되며 앞서 완료한 저장은 남습니다. 자동 재시도와 정기 실행은 포함하지 않습니다. 실패 원인을 고친 뒤 같은 기간으로 다시 실행하면 `tour_content_id` 기준으로 갱신됩니다.
