#!/usr/bin/env python3
"""
main.py – Ingestion quotidienne des news FR depuis NewsData.io vers PostgreSQL

• Filtre : uniquement les articles publiés "aujourd'hui" (UTC) 
• Pagination via nextPage
• Insertion avec ON CONFLICT pour éviter les doublons (clé = url)
• Logging propre (console + fichier optionnel)
• Sauvegarde d'un wordcloud en PNG

Variables d'environnement attendues :
  NEWSDATA_API_KEY
  PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD (optionnel si .pgpass ou autre)
  LOG_DIR (optionnel)
  HEADLESS=true|false (optionnel, par défaut true en CI/cron)
"""
from __future__ import annotations

import os
import sys
import logging
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

from src.core_logic import run_ingestion

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from src.plot_categories import generate_category_wordcloud_figure

LOGGER = logging.getLogger("wordcloud")

# ---------------------------------------------------------------------------
# Config & logging
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("LOG_DIR")
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"newsdata_{datetime.now().date()}.log")
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )

# ---------------------------------------------------------------------------
# Wordcloud
# ---------------------------------------------------------------------------

def save_wordcloud(headless: bool = True, db_url: str = None) -> str:
    """
    Génère et sauvegarde le wordcloud des catégories.

    Args:
        headless (bool): True pour environnement sans affichage.
        db_url (str, optional): URL de la base pour re-générer la figure.

    Returns:
        str: Chemin du fichier sauvegardé ou empty string si échec.
    """
    fig = generate_category_wordcloud_figure(db_url=db_url) if db_url else generate_category_wordcloud_figure()

    if headless:
        out_dir = os.getenv("OUTPUT_DIR", "outputs")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"wordcloud_{datetime.now().date()}.png")
        try:
            # Utiliser savefig pour matplotlib
            fig.savefig(out_path, dpi=300, bbox_inches='tight')
            LOGGER.info("Wordcloud sauvegardé : %s", out_path)
            return out_path
        except Exception as e:
            LOGGER.warning("Impossible d'enregistrer l'image via savefig: %s", e)
            return ""
    else:
        # affichage interactif
        plt.show()
        return ""


# ---------------------------------------------------------------------------
# Entrée
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    load_dotenv()
    setup_logging()

    headless = os.getenv("HEADLESS", "true").lower() in {"1", "true", "yes"}

    try:
        inserted = run_ingestion()
        save_wordcloud(headless=headless)
    except Exception as exc:
        logging.exception("Échec de l'ingestion : %s", exc)
        # Code de retour non nul pour CI/monitoring
        sys.exit(1)

    sys.exit(0)
