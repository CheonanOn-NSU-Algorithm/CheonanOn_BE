# 북마크 기능 작업 보고서

작성일: 2026-10-06
저장소: Merge-NSU-Algorithm/Merge_BE
기준 브랜치: develop
작업 PR: https://github.com/Merge-NSU-Algorithm/Merge_BE/pull/19

## 요약

행사 북마크 기능, 데이터베이스 마이그레이션, API 계약 정리와 테스트를 완료했다. 이 PR에는 보고서와 기능 코드가 함께 포함되며, develop에 병합되기 전 검토를 받는다.

## 구현 내용

- Bookmark 모델과 bookmarks 테이블 마이그레이션 추가
- 사용자·행사 외래 키, 삭제 연동, 사용자별 중복 북마크 방지
- JWT 인증 기반 추가·목록·삭제 API 구현
- 북마크 목록에 행사명, 이미지, 기간, 요금 유형 포함
- 팀 API 형식인 eventId 및 isBookmarked 응답 적용
- 중복 추가와 재삭제를 안전하게 처리

## API

| 기능 | 주소 | 설명 |
|---|---|---|
| 추가 | POST /api/bookmarks | eventId 또는 event_id 전달 |
| 목록 | GET /api/bookmarks | totalCount와 행사 목록 반환 |
| 삭제 | DELETE /api/bookmarks/{event_id} | 삭제 후 isBookmarked: false 반환 |

기존 호출 호환을 위해 GET /api/bookmarks/my도 유지했다. 응답은 프로젝트의 공통 success/data 형식을 사용한다.

## 데이터베이스

- 기존 cheonaon DB는 보존했다.
- 로컬 cheonaon_develop DB를 만들고 .env가 이 DB를 사용하도록 설정했다.
- 마이그레이션 a91c2d7e4b10을 적용했고, 테이블·외래 키·중복 제약을 확인했다.
- TourAPI 키가 예시값이라 자동 행사 수집은 실패했다. 키 값은 보고서에 기록하지 않았다.

## 검증 결과

- 북마크 통합 테스트 5개 통과
- 마이그레이션 버전 a91c2d7e4b10 (head) 확인
- git diff --check 통과

## 남은 작업

- GitHub develop 기준 커밋과 작업 시작 시점의 로컬 기준 커밋은 414e020으로 일치했다.
- 기존 DB 데이터는 새 DB로 복사하지 않았다.
- 실제 행사 데이터를 수집하려면 유효한 TourAPI 키를 .env에 설정하고 서버를 재시작해야 한다.
- 프론트엔드 연동은 이 저장소에서 확인하지 않았다.

## 변경 파일

- app/api/__init__.py
- app/api/bookmarks/__init__.py
- app/api/bookmarks/routes.py
- app/models/__init__.py
- app/models/bookmark.py
- app/schemas/bookmark.py
- app/services/bookmark_service.py
- migrations/versions/a91c2d7e4b10_add_bookmarks_table.py
- tests/test_bookmarks.py
