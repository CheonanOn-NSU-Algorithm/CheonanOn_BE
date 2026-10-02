"""예약 시각과 수동 수집 결과를 외부 TourAPI·운영 DB 없이 검증한다."""

import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from unittest.mock import patch

from flask import Flask

from app.extensions import db
from app.models.tour_sync_state import TourSyncState
from app.services.tour_scheduler import FestivalSyncScheduler, SYNC_INTERVAL_SECONDS
from app.services.tour_sync_state import last_success_at, record_success
import sync_festivals_manual


class StopAfterWait:
    """실제 12시간을 기다리지 않고 첫 wait에서 루프를 끝내는 테스트 대역."""

    def __init__(self):
        self.stopped = False
        self.wait_seconds = None

    def is_set(self):
        return self.stopped

    def wait(self, seconds):
        self.wait_seconds = seconds
        self.stopped = True


class TourSyncScheduleTests(unittest.TestCase):
    """성공 시각의 영속성과 재시작·실패 후 예약 동작을 확인한다."""

    def setUp(self):
        # 상태 저장 테스트는 메모리 SQLite를 사용해 실제 MySQL을 수정하지 않는다.
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        db.init_app(self.app)

    @staticmethod
    def now_utc():
        # 운영 코드처럼 시간대 정보는 제거하고 값은 UTC로 유지한다.
        return datetime.now(timezone.utc).replace(tzinfo=None)

    def test_success_time_is_persisted(self):
        """성공 기록이 없을 때는 None, 기록 후에는 같은 시각을 읽는다."""
        with self.app.app_context():
            TourSyncState.__table__.create(db.engine)
            self.assertIsNone(last_success_at())
            saved_at = record_success()
            self.assertEqual(last_success_at(), saved_at)

    def test_restart_waits_for_remaining_time(self):
        """1시간 전 성공했다면 재시작 직후 재수집하지 않고 약 11시간 기다린다."""
        scheduler = FestivalSyncScheduler()
        scheduler._stop = StopAfterWait()
        recent_success = self.now_utc() - timedelta(hours=1)
        with (
            patch("app.services.tour_scheduler.last_success_at", return_value=recent_success),
            patch("app.services.tour_scheduler.TourSyncService") as service,
        ):
            scheduler._run_loop(self.app)
        service.assert_not_called()
        self.assertAlmostEqual(scheduler._stop.wait_seconds, 11 * 60 * 60, delta=5)

    def test_due_sync_records_success(self):
        """12시간이 지났으면 수집하고 완전 성공 시각을 저장한다."""
        scheduler = FestivalSyncScheduler()
        scheduler._stop = StopAfterWait()
        now = self.now_utc()
        with (
            patch("app.services.tour_scheduler.last_success_at", side_effect=[now - timedelta(hours=13), now]),
            patch("app.services.tour_scheduler.record_success") as save_time,
            patch("app.services.tour_scheduler.TourSyncService") as service,
        ):
            service.return_value.sync_festivals.return_value = {"saved": 793, "failures": [], "complete": True}
            scheduler._run_loop(self.app)
        self.assertEqual(service.return_value.sync_festivals.call_count, 1)
        save_time.assert_called_once_with()
        self.assertAlmostEqual(scheduler._stop.wait_seconds, SYNC_INTERVAL_SECONDS, delta=5)

    def test_partial_failure_does_not_record_success(self):
        """일부 축제 실패는 DB 성공 시각을 변경하지 않는다."""
        scheduler = FestivalSyncScheduler()
        scheduler._stop = StopAfterWait()
        with (
            patch("app.services.tour_scheduler.last_success_at", return_value=None),
            patch("app.services.tour_scheduler.record_success") as save_time,
            patch("app.services.tour_scheduler.TourSyncService") as service,
        ):
            service.return_value.sync_festivals.return_value = {"saved": 1, "failures": [{}], "complete": False}
            scheduler._run_loop(self.app)
        save_time.assert_not_called()
        self.assertAlmostEqual(scheduler._stop.wait_seconds, SYNC_INTERVAL_SECONDS, delta=5)

    def test_database_error_waits_before_retry(self):
        """DB 상태 조회 실패 뒤 즉시 반복하지 않고 12시간을 기다린다."""
        scheduler = FestivalSyncScheduler()
        scheduler._stop = StopAfterWait()
        with patch("app.services.tour_scheduler.last_success_at", side_effect=RuntimeError("database unavailable")) as read_time:
            scheduler._run_loop(self.app)
        self.assertEqual(read_time.call_count, 1)
        self.assertAlmostEqual(scheduler._stop.wait_seconds, SYNC_INTERVAL_SECONDS, delta=5)

    def test_manual_run_records_only_complete_success(self):
        """별도 수동 실행도 완전 성공한 경우에만 기준 시각을 갱신한다."""
        with (
            patch("sync_festivals_manual.create_app", return_value=self.app),
            patch("sync_festivals_manual.TourSyncService") as service,
            patch("sync_festivals_manual.record_success") as save_time,
            redirect_stdout(StringIO()),
        ):
            service.return_value.sync_festivals.return_value = {"saved": 2, "failures": [], "complete": True}
            self.assertEqual(sync_festivals_manual.main(), 0)
            save_time.assert_called_once_with()

            save_time.reset_mock()
            service.return_value.sync_festivals.return_value = {"saved": 1, "failures": [{}], "complete": False}
            self.assertEqual(sync_festivals_manual.main(), 1)
            save_time.assert_not_called()


if __name__ == "__main__":
    unittest.main()
