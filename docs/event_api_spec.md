# 행사 조회 API 명세서

현재 브랜치에서 구현된 공개 행사 조회 API입니다. 기존 계획서의 천안 전용 `event` 테이블 대신 전국 행사 `events` 테이블을 사용합니다. 인증과 외부 TourAPI 호출 없이 수집된 DB 데이터를 조회합니다. 응답 필드는 아래와 같이 `CommonResponse`의 `data` 안에 들어갑니다.

## 1. 행사 목록

`GET /api/v1/event`

### 쿼리 파라미터

| 이름 | 형식 | 기본값 | 설명 |
|---|---|---|---|
| `q` | 문자열, 최대 100자 | 없음 | 행사명·장소·태그 이름의 일부 검색. 앞뒤 공백은 제거합니다. `%`, `_`는 일반 문자로 검색합니다. |
| `category_id` | 1 이상의 정수 | 없음 | `categories.id`와 일치하는 행사만 조회합니다. |
| `sido_code` | 두 자리 숫자 문자열 | 없음 | `sidos.code`와 일치하는 행사만 조회합니다. 예: `44`는 충남. |
| `is_free` | 불리언 (`true`/`false`) | 없음 | 무료 여부로 필터링합니다. 값이 불명확한 `NULL` 행은 두 조건에서 제외됩니다. |
| `start_date` | `YYYY-MM-DD` | 없음 | 행사 종료일이 이 날짜 이상인 행사를 조회합니다. |
| `end_date` | `YYYY-MM-DD` | 없음 | 행사 시작일이 이 날짜 이하인 행사를 조회합니다. |
| `sort` | `latest`, `popular`, `dateAsc` | `latest` | 각각 등록일 내림차순, 누적 조회수 내림차순, 시작일 오름차순입니다. 동률이면 ID로 순서를 고정합니다. |
| `page` | 1 이상의 정수 | `1` | 페이지 번호 |
| `size` | 1~100의 정수 | `20` | 페이지당 행사 수 |

두 날짜를 함께 보내면 입력한 기간과 하루라도 겹치는 행사를 조회합니다. `start_date`가 `end_date`보다 늦으면 400 오류입니다. `popular`는 현재 `events.view_count`의 **누적값** 기준이며 주간 순위가 아닙니다.

### 요청 예시

```http
GET /api/v1/event?q=축제&sido_code=44&page=1&size=20
```

### 성공 응답: 200

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

`totalCount`는 현재 페이지 수가 아닌 전체 필터 결과 수입니다. 검색 결과가 없으면 `totalCount`는 `0`, `events`는 빈 배열입니다. 행사 카드의 `venueName`, `thumbnailUrl`, `price`, `isFree`는 DB 값이 없으면 `null`입니다. 응답 예시는 형식을 설명하기 위한 가상 데이터입니다.

## 2. 행사 상세

`GET /api/v1/event/<id>`

`id`는 TourAPI `contentid`가 아닌 `events.id` 정수 기본키입니다. 목록 카드의 `id`를 그대로 전달합니다.

### 성공 응답: 200

```json
{
  "success": true,
  "message": "OK",
  "data": {
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
    "description": "행사 소개",
    "address": "충청남도 예시 주소",
    "addressDetail": null,
    "playTime": null,
    "feeText": "무료",
    "imageUrl": null,
    "latitude": 36.0,
    "longitude": 127.0,
    "organizer": null,
    "contactPhone": null,
    "homepageUrl": null,
    "isPermanent": false
  }
}
```

상세 조회는 현재 `view_count`와 `event_daily_views`를 증가시키지 않습니다. 찜 여부, 리뷰 수, 평점, 길찾기 결과도 현재 응답에 없습니다.

## 3. 오류 응답

잘못된 쿼리 파라미터는 400 `COMMON_INVALID_INPUT`으로 응답하며, `fields`에 필드별 오류를 담습니다.

```json
{
  "success": false,
  "code": "COMMON_INVALID_INPUT",
  "message": "요청 값이 올바르지 않습니다.",
  "fields": {
    "page": ["Must be greater than or equal to 1."]
  }
}
```

없는 정수 행사 ID는 404 `EVENT_NOT_FOUND`로 응답합니다.

```json
{
  "success": false,
  "code": "EVENT_NOT_FOUND",
  "message": "존재하지 않는 행사입니다."
}
```

라우트에 일치하지 않는 경로·메서드는 Flask의 공통 HTTP 오류 핸들러로 응답합니다. 이 API에 별도 DB 마이그레이션은 필요하지 않습니다.
