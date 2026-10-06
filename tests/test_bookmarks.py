import os
import unittest
from datetime import date

# 테스트는 실제 DB 설정과 분리된 메모리 SQLite만 사용한다.
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "bookmark-tests-only-secret-key-32-bytes"

from flask_jwt_extended import create_access_token

from app import create_app
from app.extensions import db
from app.models.bookmark import Bookmark
from app.models.tour_content import Category, Event, Sido
from app.models.user import User


class BookmarkApiTests(unittest.TestCase):
    """실제 MySQL 설정과 분리한 메모리 DB에서 북마크 API를 검증한다."""

    @classmethod
    def setUpClass(cls):
        """테스트 전체에서 앱과 테스트 클라이언트를 한 번만 만든다."""
        cls.app = create_app()
        cls.app.config.update(TESTING=True)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        """테스트 종료 후 DB 세션과 연결을 정리한다."""
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def setUp(self):
        """각 테스트 전에 사용자 두 명과 행사 한 건으로 독립된 DB를 준비한다."""
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

        self.user = User(kakao_id=101, email="bookmark@example.com", nickname="tester")
        self.other_user = User(kakao_id=102, email="other@example.com", nickname="other")
        category = Category(name="축제", sort_order=1)
        sido = Sido(code="11", name="서울특별시", short_name="서울", sort_order=1)
        db.session.add_all([self.user, self.other_user, category, sido])
        db.session.flush()

        self.event = Event(
            tour_content_id="event-1",
            category_id=category.id,
            sido_code=sido.code,
            title="테스트 행사",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 2),
        )
        db.session.add(self.event)
        db.session.commit()

        self.token = create_access_token(identity=str(self.user.id))
        self.other_token = create_access_token(identity=str(self.other_user.id))
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        """테스트 데이터를 지우고 앱 컨텍스트를 종료한다."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_list_and_delete_bookmark(self):
        """추가 응답, 목록 조회, 삭제까지 기본 흐름을 확인한다."""
        created = self.client.post(
            "/api/bookmarks",
            json={"eventId": self.event.id},
            headers=self.auth_headers,
        )
        self.assertEqual(created.status_code, 201)
        created_data = created.get_json()["data"]
        self.assertEqual(created_data["eventId"], self.event.id)
        self.assertTrue(created_data["isBookmarked"])

        listed = self.client.get("/api/bookmarks", headers=self.auth_headers)
        self.assertEqual(listed.status_code, 200)
        listing_data = listed.get_json()["data"]
        self.assertEqual(listing_data["totalCount"], 1)
        self.assertEqual(listing_data["events"][0]["id"], self.event.id)
        self.assertEqual(listing_data["events"][0]["title"], self.event.title)

        deleted = self.client.delete(
            f"/api/bookmarks/{self.event.id}", headers=self.auth_headers
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(Bookmark.query.count(), 0)

    def test_duplicate_bookmark_is_idempotent(self):
        """입력 표기가 달라도 재요청 시 중복 행이 생기지 않는지 확인한다."""
        first = self.client.post(
            "/api/bookmarks", json={"eventId": self.event.id}, headers=self.auth_headers
        )
        second = self.client.post(
            "/api/bookmarks", json={"event_id": self.event.id}, headers=self.auth_headers
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["data"], second.get_json()["data"])
        self.assertEqual(Bookmark.query.count(), 1)

    def test_users_only_see_their_own_bookmarks(self):
        """다른 사용자의 북마크가 목록에 노출되지 않는지 확인한다."""
        self.client.post(
            "/api/bookmarks", json={"eventId": self.event.id}, headers=self.auth_headers
        )
        response = self.client.get(
            "/api/bookmarks",
            headers={"Authorization": f"Bearer {self.other_token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"], {"totalCount": 0, "events": []})

    def test_missing_event_is_not_found_and_delete_is_idempotent(self):
        """없는 행사는 404이고 없는 북마크를 지워도 성공인지 확인한다."""
        missing_event = self.client.post(
            "/api/bookmarks", json={"event_id": 99999}, headers=self.auth_headers
        )
        self.assertEqual(missing_event.status_code, 404)
        self.assertEqual(missing_event.get_json()["code"], "EVENT_NOT_FOUND")

        missing_bookmark = self.client.delete(
            f"/api/bookmarks/{self.event.id}", headers=self.auth_headers
        )
        self.assertEqual(missing_bookmark.status_code, 200)
        self.assertEqual(missing_bookmark.get_json()["data"], {
            "eventId": self.event.id,
            "isBookmarked": False,
        })

    def test_bookmark_endpoints_require_authentication(self):
        """인증 토큰이 없는 요청을 거부하는지 확인한다."""
        response = self.client.get("/api/bookmarks")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
