import os
import requests
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv

from src.plot_categories import generate_category_wordcloud_figure

load_dotenv()
API_KEY = os.getenv("NEWSDATA_API_KEY")

# Heure actuelle (UTC) → début du jour
today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

# Connexion PostgreSQL
conn = psycopg2.connect(
    dbname="newsdata",
    user="postgres",
    password="admin",  # adapte à ton cas
    host="localhost",
    port="5432"
)
cur = conn.cursor()

url = "https://newsdata.io/api/1/news"
total_inserted = 0
page_token = None

while True:
    params = {
        "apikey": API_KEY,
        "country": "fr",
        "language": "fr"
    }
    if page_token:
        params["page"] = page_token

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("status") != "success":
        print(f"Erreur API : {data.get('results', {}).get('message') or data}")
        break

    articles = data.get("results", [])
    if not articles:
        print("Aucune donnée reçue, arrêt.")
        break

    for art in articles:
        pub_str = art.get("pubDate")
        try:
            pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            pub_date = None

        if pub_date < today_utc:
            continue  # filtré : article antérieur à aujourd'hui

        cur.execute("""
            INSERT INTO articles_fr (
                title, url, source, category, published_at
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
        """, (
            art.get("title"),
            art.get("link"),
            art.get("source_id"),
            art.get("category", [None])[0] if art.get("category") else None,
            pub_date
        ))
        total_inserted += 1

    print(f"{len(articles)} articles insérés depuis page {page_token or '1'}.")

    # Pagination via nextPage
    page_token = data.get("nextPage")
    if not page_token:
        print("Toutes les pages ont été traitées.")
        break

conn.commit()
cur.close()
conn.close()

print(f"\nTotal inséré : {total_inserted} articles.")
fig = generate_category_wordcloud_figure()
fig.show()