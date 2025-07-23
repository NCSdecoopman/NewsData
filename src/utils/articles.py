from datetime import datetime, timezone
from typing import Optional

from psycopg2.extras import execute_batch


def parse_pub_date(pub_str: Optional[str]) -> Optional[datetime]:
    if not pub_str:
        return None
    try:
        # NewsData renvoie souvent un ISO 8601 avec Z
        return datetime.fromisoformat(pub_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:  # pragma: no cover - robustesse
        return None


def insert_articles(cur, rows):
    sql = """
        INSERT INTO articles_fr (title, url, source, category, published_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING;
    """
    execute_batch(cur, sql, rows, page_size=500)


def should_save_today(pub_date: Optional[datetime], today_utc: datetime) -> bool:
    if pub_date is None:
        return False
    return pub_date >= today_utc