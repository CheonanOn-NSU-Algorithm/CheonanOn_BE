# 북마크 기능 작업 보고서

작성일: 2026-10-06  
저장소: `Merge-NSU-Algorithm/Merge_BE`  
기준 브랜치: `develop`

## 요약

행사 북마크 기능, 데이터베이스 마이그레이션, API 계약 정리와 테스트를 완료했다. 이 PR에는 작업 보고서만 포함하며, 기능 코드 변경은 별도로 로컬 `develop` 브랜치에 남아 있다.

## 구현 내용

- `Bookmark` 모델과 `bookmarks` 테이블 마이그레이션 추가
- 사용자·행사 외래 키, 삭제 연동, 사용자별 중복 북마크 방지
- JWT 인증 기반 추가·목록·삭제 API 구현
- 북마크 목록에 행사명, 이미지, 기간, 요금 유형 포함
- 팀 API 형식인 `eventId` 및 `isBookmarked` 응답 적용
- 중복 추가와 재삭제를 안전하게 처리

## API

| 기능 | 주소 | 설명 |
|---|---|---|
| 추가 | `POST /api/bookmarks` | `eventId` 또는 `event_id` 전달 |
| 목록 | `GET /api/bookmarks` | `totalCount`와 행사 목록 반환 |
| 삭제 | `DELETE /api/bookmarks/{event_id}` | 삭제 후 `isBookmarked: false` 반환 |

기존 호출 호환을 위해 `GET /api/bookmarks/my`도 유지했다. 응답은 프로젝트의 공통 `success/data` 형식을 사용한다.

## 데이터베이스

- 기존 `cheonaon` DB는 보존했다.
- 로컬 `cheonaon_develop` DB를 만들고 `.env`가 이 DB를 사용하도록 설정했다.
- 마이그레이션 `a91c2d7e4b10`을 적용했고, 테이블·외래 키·중복 제약을 확인했다.
- TourAPI 키가 예시값이라 자동 행사 수집은 실패했다. 키 값은 보고서에 기록하지 않았다.

## 검증 결과

- 북마크 통합 테스트 5개 통과
- 마이그레이션 버전 `a91c2d7e4b10 (head)` 확인
- `git diff --check` 통과

## 남은 작업

- 기능 코드 변경은 아직 커밋·푸시하지 않았다.
- GitHub와 로컬 `develop` 기준 커밋은 `414e020`으로 일치했다.
- 기존 DB 데이터를 새 DB로 복사하지 않았다.
- 실제 행사 데이터를 수집하려면 유효한 TourAPI 키를 `.env`에 설정하고 서버를 재시작해야 한다.
- 프론트엔드 연동은 이 저장소에서 확인하지 않았다.

## 변경 파일

- `app/models/bookmark.py`
- `app/api/bookmarks/routes.py`
- `app/services/bookmark_service.py`
- `app/schemas/bookmark.py`
- `migrations/versions/a91c2d7e4b10_add_bookmarks_table.py`
- `tests/test_bookmarks.py`
