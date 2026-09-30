# 행사 조회 API 명세서

기본 주소는 `http://127.0.0.1:5000`입니다. 아래 API는 인증과 요청 본문 없이 수집된 DB 데이터를 조회합니다. 성공 응답은 `{"success": true, "message": "OK", "data": ...}` 형식입니다. 응답 예시의 행사와 숫자는 가상 데이터입니다.

| 경로 | 기능 |
|---|---|
| `GET /api/v1/event` | 행사 목록·검색·필터·페이지 조회 |
| `GET /api/v1/event/<id>` | 행사 상세 조회와 조회수 기록 |
| `GET /api/v1/event/monthly-top` | 월간 조회수 상위 축제 |
| `GET /api/v1/event/categories` | 카테고리 선택지 |
| `GET /api/v1/event/sidos` | 시도 선택지 |

정의되지 않은 쿼리 키와 동일한 키의 반복은 `400 COMMON_INVALID_INPUT`입니다. 상세·선택지 API에는 쿼리 파라미터를 붙이지 않습니다. 사용하지 않는 필터는 빈 문자열로 보내지 말고 생략합니다. `HEAD`는 조회수를 기록하지 않으며 `OPTIONS`는 Flask가 허용 메서드를 안내합니다.

## 1. 행사 목록

`GET /api/v1/event`

| 이름 | 형식 | 기본값 | 설명 |
|---|---|---|---|
| `q` | 문자열, 최대 100자 | 없음 | 행사명·장소·태그 이름 검색. 앞뒤 공백 제거. `%`, `_`는 일반 문자로 검색 |
| `category_id` | 1~2,147,483,647의 정수 | 없음 | `categories.id`와 일치하는 행사 |
| `sido_code` | 두 자리 숫자 문자열 | 없음 | `sidos.code`와 일치하는 행사. 예: `44`는 충남 |
| `is_free` | 소문자 `true` 또는 `false` | 없음 | 무료 여부. DB 값이 `NULL`이면 어느 쪽에도 포함되지 않음 |
| `start_date` | `YYYY-MM-DD` | 없음 | 행사 종료일이 이 날짜 이상 |
| `end_date` | `YYYY-MM-DD` | 없음 | 행사 시작일이 이 날짜 이하 |
| `sort` | `latest`, `popular`, `dateAsc` | `latest` | 등록일 내림차순, 누적 조회수 내림차순, 시작일 오름차순 |
| `page` | 1~2,147,483,647의 정수 | `1` | 페이지 번호 |
| `size` | 1~100의 정수 | `20` | 페이지당 행사 수 |

두 날짜를 함께 보내면 조회 기간과 하루라도 겹치는 행사를 찾습니다. 시작일이 종료일보다 늦으면 400입니다. `latest`·`popular`의 동률은 행사 ID 내림차순, `dateAsc`의 동률은 ID 오름차순입니다. `popular`는 `events.view_count` 누적값을 사용합니다. 존재하지 않는 카테고리·시도 ID는 정상적인 빈 결과입니다.

```http
GET /api/v1/event?q=축제&sido_code=44&page=1&size=20
```

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "totalCount": 1,
    "page": 1,
    "size": 20,
    "events": [
      {
        "id": 1,
        "title": "예시 축제",
        "categoryId": 1,
        "category": "축제",
        "sidoCode": "44",
        "sido": "충남",
        "startDate": "2026-10-01",
        "endDate": "2026-10-03",
        "venueName": "예시 행사장",
        "thumbnailUrl": null,
        "price": 0,
        "isFree": true
      }
    ]
  }
}
```

`totalCount`는 현재 페이지 수가 아니라 전체 필터 결과 수입니다. 마지막 페이지를 넘어가면 `events`만 빈 배열이고 `totalCount`는 유지됩니다. 결과가 아예 없으면 `totalCount`는 0입니다. 카드의 `venueName`, `thumbnailUrl`, `price`, `isFree`는 DB 값이 없을 때 `null`입니다.

## 2. 행사 상세

`GET /api/v1/event/<id>`의 `id`는 TourAPI의 `contentid`가 아닌 목록 카드의 `events.id`입니다. 1~2,147,483,647을 허용합니다. 범위 안의 없는 ID는 `404 EVENT_NOT_FOUND`입니다.

상세 `data`에는 목록 카드의 필드와 `description`, `address`, `addressDetail`, `playTime`, `feeText`, `imageUrl`, `latitude`, `longitude`, `organizer`, `contactPhone`, `homepageUrl`, `isPermanent`가 들어갑니다. 정보가 없는 선택 필드는 `null`입니다.

정상적인 상세 GET마다 `events.view_count`와 한국 날짜의 `event_daily_views.view_count`가 각각 1씩 증가합니다. 같은 사용자의 반복 조회도 매번 집계합니다. 목록·선택지·월간 순위·HEAD·OPTIONS와 없는 행사 조회는 집계하지 않습니다. 두 집계는 한 트랜잭션으로 저장하며 실패하면 모두 롤백합니다. MySQL에서는 행사 행 잠금으로 같은 행사에 대한 동시 요청을 순차 처리합니다. 조회수 기록은 `events.updated_at`을 바꾸지 않습니다. DB 저장 후 응답 전달이 실패해도 해당 조회는 집계될 수 있습니다.

## 3. 월간 최고의 축제

`GET /api/v1/event/monthly-top`

| 이름 | 형식 | 기본값 | 설명 |
|---|---|---|---|
| `month` | `YYYY-MM` | 한국 시간 기준 이번 달 | 조회할 달 |
| `size` | 1~20의 정수 | `4` | 반환할 축제 수 |

선택한 달의 일별 조회수를 행사별로 합산합니다. `categories.name`이 `축제`이고 해당 월 합계가 1 이상인 행사만 조회수 내림차순으로 반환합니다. 동률은 행사 ID 내림차순입니다. 행사 진행 기간은 순위 조건이 아닙니다. 일별 조회수 기록이 없으면 빈 배열입니다. 과거 누적 조회수를 일별 조회수로 복원하지 않습니다.

```http
GET /api/v1/event/monthly-top?month=2026-09&size=4
```

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "month": "2026-09",
    "events": [
      {
        "id": 1,
        "title": "예시 축제",
        "categoryId": 1,
        "category": "축제",
        "sidoCode": "44",
        "sido": "충남",
        "startDate": "2026-10-01",
        "endDate": "2026-10-03",
        "venueName": "예시 행사장",
        "thumbnailUrl": null,
        "price": 0,
        "isFree": true,
        "monthlyViews": 15
      }
    ]
  }
}
```

`monthlyViews`는 해당 월의 조회수이며 목록의 `sort=popular`에서 사용하는 누적 조회수와 다릅니다.

## 4. 카테고리·시도 선택지

`GET /api/v1/event/categories`는 `sort_order`, `id` 오름차순의 `{ "id", "name", "sortOrder" }` 배열을 `data`에 반환합니다.

`GET /api/v1/event/sidos`는 `sort_order`, `code` 오름차순의 `{ "code", "name", "shortName", "sortOrder" }` 배열을 `data`에 반환합니다. 예: `{ "code": "44", "name": "충청남도", "shortName": "충남", "sortOrder": 5 }`.

카테고리 `id`와 시도 `code`를 목록 조회의 `category_id`, `sido_code`에 각각 전달합니다. 전체를 선택한 경우 해당 조건을 생략합니다. 기준 테이블이 비면 빈 배열을 반환하며 선택지 조회는 행사 조회수를 증가시키지 않습니다.

## 5. 오류 응답

| 상태 | code | 원인 |
|---|---|---|
| 400 | `COMMON_INVALID_INPUT` | 값의 타입·형식·범위, 알 수 없는 키, 중복 키 |
| 404 | `EVENT_NOT_FOUND` | 범위 안의 행사 ID가 DB에 없음 |
| 404 | `Not Found` | 등록되지 않은 URL 또는 정수가 아닌 상세 경로 |
| 405 | `Method Not Allowed` | 허용되지 않은 메서드. `Allow` 헤더 포함 |
| 503 | `COMMON_DB_UNAVAILABLE` | DB 접속·연결 풀·일시적인 잠금 장애 |
| 500 | `COMMON_INTERNAL_ERROR` | 기타 DB 실행 오류·예상하지 못한 오류 |

검증 오류는 `fields`에 필드별 사유를 담습니다.

```json
{
  "success": false,
  "code": "COMMON_INVALID_INPUT",
  "message": "요청 값이 올바르지 않습니다.",
  "fields": { "page": ["Must be greater than or equal to 1 and less than or equal to 2147483647."] }
}
```

DB 연결 수 초과(1040), 잠금 대기·교착(1205/1213), 연결 오류(2002/2003/2005/2006/2013), 연결 풀 대기 시간 초과와 감지된 연결 단절은 503입니다. `pool_pre_ping`은 풀에서 꺼낸 연결을 확인하지만 실패한 조회수 저장을 자동 재실행하지 않습니다. 상세 SQL·접속 정보·원본 예외는 응답에 포함되지 않고 서버 로그에 남습니다.
