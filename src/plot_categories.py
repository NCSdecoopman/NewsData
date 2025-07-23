import pandas as pd
from sqlalchemy import create_engine
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from src.utils.translate import translate_text

def generate_category_wordcloud_figure(
    db_url: str = "postgresql+psycopg2://postgres:admin@localhost:5432/newsdata"
) -> plt.Figure:
    """
    Génère un nuage de mots pondéré des catégories d'articles, traduit en français.

    Args:
        db_url (str): URL de connexion SQLAlchemy à la base PostgreSQL.

    Returns:
        matplotlib.figure.Figure: Figure contenant le nuage de mots.
    """
    # Connexion base
    engine = create_engine(db_url)
    df = pd.read_sql("SELECT category FROM articles_fr WHERE category IS NOT NULL", con=engine)
    df = df[~df["category"].isin(["top", "other"])]

    # Comptage
    category_counts = df['category'].value_counts()

    # Traduction + capitalisation
    translated_index = [translate_text(cat).capitalize() for cat in category_counts.index]
    translated_freq = dict(zip(translated_index, category_counts.values))

    # Création du wordcloud
    wordcloud = WordCloud(width=1200, height=600, background_color='white').generate_from_frequencies(translated_freq)

    # Génération de la figure
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    ax.set_title("Répartition des articles par catégorie", fontsize=16)
    plt.tight_layout()

    return fig
