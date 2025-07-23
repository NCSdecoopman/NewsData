import os
import time
import random
import logging
from datetime import datetime, timezone
from typing import Optional

import requests
from requests.exceptions import HTTPError, RequestException

from src.utils.articles import parse_pub_date, should_save_today, insert_articles
from src.utils.db_helper import get_pg_conn

LOGGER = logging.getLogger("ingestion")

# -------- Configurable constants -------- #
MAX_RETRIES = 2                 # nombre max de retries sur 429/erreurs transitoires
PAGE_SLEEP_SECONDS = 0.5        # pause minimale entre deux pages
STOP_WHEN_OLD = True            # arrêter quand on tombe hors de la fenêtre du jour


def fetch_articles(
    api_key: str,
    page_token: Optional[str] = None,
    session: Optional[requests.Session] = None,
    max_retries: int = MAX_RETRIES,
) -> dict:
    """Appelle l'API Newsdata avec gestion du 429 (backoff + Retry-After) et erreurs réseau."""
    url = "https://newsdata.io/api/1/news"
    params = {"apikey": api_key, "country": "fr", "language": "fr"}
    if page_token:
        params["page"] = page_token

    sess = session or requests.Session()
    attempt = 0

    while True:
        try:
            resp = sess.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status == 429 and attempt < max_retries:
                retry_after = e.response.headers.get("Retry-After") if e.response else None
                sleep_s = int(retry_after) if retry_after else (2 ** attempt) + random.uniform(0, 1)
                LOGGER.warning("429 reçu, retry dans %.2fs (tentative %s/%s)", sleep_s, attempt + 1, max_retries)
                time.sleep(sleep_s)
                attempt += 1
                continue
            # autre erreur HTTP ou trop de tentatives -> on propage
            raise
        except RequestException as e:
            # erreurs réseau transitoires
            if attempt < max_retries:
                sleep_s = (2 ** attempt) + random.uniform(0, 1)
                LOGGER.warning("Erreur réseau '%s', retry dans %.2fs (tentative %s/%s)", e, sleep_s, attempt + 1, max_retries)
                time.sleep(sleep_s)
                attempt += 1
                continue
            # trop de retries -> on propage
            raise


def run_ingestion() -> int:
    """Récupère et insère les articles du jour, abandonne proprement si limite API ou erreurs réseau finales."""
    api_key = os.getenv("NEWSDATA_API_KEY")
    if not api_key:
        LOGGER.error("NEWSDATA_API_KEY manquant.")
        raise SystemExit(1)

    today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_inserted = 0
    page_token = None
    stop_after_old = False

    session = requests.Session()

    with get_pg_conn() as conn, conn.cursor() as cur:
        while True:
            # Tentative de fetch, gestion des erreurs finales
            try:
                data = fetch_articles(api_key, page_token, session=session)
            except HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    LOGGER.error("Limite API journalière atteinte, abandon de l'ingestion de nouveaux articles.")
                    break
                LOGGER.error("Erreur HTTP finale : %s", e)
                break
            except RequestException as e:
                LOGGER.error("Erreur réseau finale, abandon de l'ingestion : %s", e)
                break

            if data.get("status") != "success":
                LOGGER.error("Erreur API : %s", data)
                break

            articles = data.get("results", []) or []
            if not articles:
                LOGGER.info("Aucune donnée reçue, arrêt.")
                break

            batch_rows = []
            for art in articles:
                pub_date = parse_pub_date(art.get("pubDate"))
                if not should_save_today(pub_date, today_utc):
                    if STOP_WHEN_OLD:
                        stop_after_old = True
                    continue

                batch_rows.append(
                    (
                        art.get("title"), art.get("link"), art.get("source_id"),
                        (art.get("category") or [None])[0], pub_date,
                    )
                )

            if batch_rows:
                insert_articles(cur, batch_rows)
                conn.commit()
                total_inserted += len(batch_rows)
                LOGGER.info("%s articles insérés (page %s).", len(batch_rows), page_token or "1")
            else:
                LOGGER.info("0 article inséré sur cette page (filtrage par date).")

            if stop_after_old:
                LOGGER.info("Fin : plus d'articles du jour.")
                break

            page_token = data.get("nextPage")
            if not page_token:
                LOGGER.info("Toutes les pages ont été traitées.")
                break

            time.sleep(PAGE_SLEEP_SECONDS)

    LOGGER.info("Total inséré : %s articles.", total_inserted)
    return total_inserted
