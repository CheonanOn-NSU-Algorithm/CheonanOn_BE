from app.extensions import db
from app.models.event import Bookmark, Event


class BookmarkService:

    @staticmethod
    def create_bookmark(user_id, event_id):
        event = db.session.get(Event, event_id)

        if event is None:
            return None

        bookmark = db.session.get(
            Bookmark,
            (user_id, event_id)
        )

        if bookmark is not None:
            return {
                "eventId": event_id,
                "isBookmarked": True,
            }

        bookmark = Bookmark(
            user_id=user_id,
            event_id=event_id,
        )

        db.session.add(bookmark)
        db.session.commit()

        return {
            "eventId": event_id,
            "isBookmarked": True,
        }

    @staticmethod
    def delete_bookmark(user_id, event_id):
        bookmark = db.session.get(
            Bookmark,
            (user_id, event_id)
        )

        if bookmark is not None:
            db.session.delete(bookmark)
            db.session.commit()

        return {
            "eventId": event_id,
            "isBookmarked": False,
        }

    @staticmethod
    def get_bookmarks(user_id):
        rows = (
            db.session.query(Bookmark, Event)
            .join(Event, Bookmark.event_id == Event.id)
            .filter(Bookmark.user_id == user_id)
            .order_by(Bookmark.created_at.desc())
            .all()
        )

        events = []

        for bookmark, event in rows:
            events.append({
                "id": event.id,
                "title": event.title,
                "imageUrl": (
                    event.thumbnail_url
                    or event.image_url
                ),
                "startDate": event.start_date,
                "endDate": event.end_date,
                "priceType": (
                    "FREE"
                    if event.is_free
                    else "PAID"
                ),
            })

        return {
            "totalCount": len(events),
            "events": events,
        }