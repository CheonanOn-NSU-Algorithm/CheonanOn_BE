2026/09/30


feature/bookmark-yeonjoon-hyunjin-mixed

북마크 테이블 migration 추가했고, feature/bookmark-yeonjoon-hyunjin-mixed 브랜치에 push했습니다.


### 북마크 CRUD

북마크 기능은 행사에 대한 사용자의 저장 상태를 관리합니다.

| 구분 | 기능 | API |
|---|---|---|
| Create | 행사 북마크 추가 | `POST /api/v1/bookmarks` |
| Read | 내가 저장한 북마크 목록 조회 | `GET /api/v1/bookmarks` |
| Update | 별도의 수정 대상 속성이 없어 제공하지 않음 | - |
| Delete | 행사 북마크 삭제 | `DELETE /api/v1/bookmarks/{eventId}` |

북마크는 `user_id`와 `event_id`를 기준으로 저장되며,
두 컬럼을 복합 기본키로 설정하여 동일 사용자의 동일 행사 중복 저장을 방지합니다.


북마크 API는 app/api/bookmarks, 비즈니스 로직은 app/services/bookmark_service.py, 북마크 모델은 기존 app/models/event.py에 추가했고, 요청/응답은 app/schemas/bookmark.py, DB 테이블 생성은 migrations/versions/20260929_add_bookmarks_table.py에서
