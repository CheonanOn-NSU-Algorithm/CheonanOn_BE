"""필요할 때 한 번 실행하는 전국 축제 DB 갱신 명령.

프로젝트 루트에서 ``python sync_festivals_manual.py``로 실행한다.
TourAPI 목록과 각 축제의 상세를 조회해 기존 TourSyncService로 events에
추가·갱신하고, 전체 성공 후 지난 행사를 정리한다. 웹서버와 예약 작업은 이 파일을 import하지 않는다.
따라서 이 파일만 별도로 제거해도 본편의 API·자동 갱신에는 영향이 없다.
"""

import json

from app import create_app
from app.errors import BusinessException, ErrorCode
from app.services.tour_sync import TourSyncService
from app.services.tour_sync_state import record_success


def main():
    """전국 축제를 한 번 수집하고 성공이면 0, 실패가 있으면 1을 반환한다.

    결과 JSON에는 저장 건수(saved), 실패 항목(failures), 전체 성공 여부
    (complete)가 들어간다. 부분 실패 시 이미 저장된 행은 유지된다.
    """
    # 앱 객체만 만들고 웹서버를 시작하지 않는다. wsgi.py의 __main__ 블록을
    # 실행하지 않으므로 자동 예약 스레드도 이 명령 때문에 시작되지 않는다.
    app = create_app()
    try:
        # HTTP 요청 밖에서 db.engine을 사용하려면 Flask 앱 컨텍스트가 필요하다.
        # 자동 갱신과 같은 서비스를 써서 같은 tour_content_id의 축제가
        # 중복 INSERT되지 않고 기존 events 행에 갱신되도록 한다.
        with app.app_context():
            report = TourSyncService().sync_festivals()
            # sync_festivals()는 건별 오류를 failures에 기록하고 다음 건을
            # 처리한다. 예외가 없더라도 complete=False일 수 있으므로
            # 전체 성공을 확인한 뒤에만 12시간 기준 시각을 DB에 남긴다.
            if report["complete"]:
                record_success()
    except BusinessException as error:
        # 서비스가 분류한 오류는 app/errors의 코드·메시지·부가 정보를
        # 그대로 출력한다. 작업자가 종료 코드 1로 실패를 확인할 수 있다.
        print(json.dumps({"code": error.error_code.code, "message": error.message, "extra": error.extra}, ensure_ascii=False))
        return 1
    except Exception:
        # DB 연결 장애나 예상 못한 오류의 traceback은 로그에 남긴다.
        # 콘솔 JSON에는 내부 예외 문자열이나 접속 정보를 노출하지 않는다.
        app.logger.exception("수동 축제 갱신 중 오류가 발생했습니다.")
        print(json.dumps({"code": ErrorCode.COMMON_INTERNAL_ERROR.code, "message": ErrorCode.COMMON_INTERNAL_ERROR.message}, ensure_ascii=False))
        return 1

    # 건별 실패도 종료 코드 1로 알린다. 같은 기간을 다시 실행하면
    # tour_content_id 기준으로 기존 성공 건은 갱신하고 실패 건은 재시도한다.
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    # import만 하는 경우에는 수집하지 않고, 파일을 직접 실행할 때만 동작한다.
    raise SystemExit(main())
