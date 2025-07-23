# NewsData – Pipeline des informations quotidiennes populaires françaises

Récupération quotidienne des 200 articles les plus populaires en France, stockage en PostgreSQL et visualisations rapides des thématiques émergentes.

---

## Objectifs

* **Interroger l’API NewsData.io**.
* **Filtrer les articles du jour** (≥ 00:00 UTC) et insérer en base.
* **Stocker en SQL** seulement les champs utiles (`title`, `link`, `source`, `category`, `pubDate`).
* **Traduire** les catégories EN → FR en local (Argos Translate).
* **Visualiser** la répartition des catégories (nuage de mots).

---

## Arborescence

```
NewsData/
├── .github/workflow/maj.yml        # Automatisation quotidienne
├── .env
├── .gitignore
├── db.sql                          # Création de la table articles_fr
├── main.py                         # Pipeline d’ingestion + filtre "aujourd’hui"
├── requirements.txt
├── src/
|   ├── core_logic.py  
│   ├── plot_categories.py          # generate_category_wordcloud_figure()
│   └── utils/
|       ├── articles.py
|       ├── db_helper.py
│       └── translate.py
└── README.md
```

## Stack technique

* **Python** (géré via [`uv`](https://github.com/astral-sh/uv))
* **PostgreSQL** (local)
* **API Request**
* **CI/CD** GitHub Actions pour l'automatisation journalière

---

## Installation rapide

### 1. Cloner & créer l’environnement

```bash
git clone https://github.com/NCSdecoopman/NewsData.git
cd NewsData
uv venv env
source env/bin/activate            # (Linux/Mac)
# .\env\Scripts\Activate.ps1     # (Windows PowerShell)
```

### 2. Installer les dépendances

```bash
uv pip install -r requirements.txt
```

### 3. Variables d’environnement

Crée un fichier `.env` à la racine :

```env
NEWSDATA_API_KEY=ta_cle_api
```

> `.env` est ignoré par Git (cf. `.gitignore`).

### 4. Initialiser la base PostgreSQL

```bash
psql -U postgres -c "CREATE DATABASE newsdata;"
psql -U postgres -d newsdata -f db.sql
```

---

## Exécuter le pipeline

```bash
python main.py
```

* Récupère toutes les pages via le jeton `nextPage`.
* Filtre les articles publiés **aujourd’hui** (UTC).
* Insère dans `articles_fr` avec `ON CONFLICT (url) DO NOTHING`.
* À la fin, génère un nuage de mots.

---

## Traduction offline (Argos Translate)

Dans `src/utils/translate.py` :

* `install_if_needed(source, target)` vérifie/installe le modèle EN→FR la première fois
* `translate_text(text)` traduit ensuite localement (aucune clé API)

---

## Idées d’extension

* [ ] Déploiement de la base de données sur AWS, GCP, etc.
* [ ] Ajouter un **dashboard Streamlit** (top sources, timeline par jour)
* [ ] Stocker aussi le **sentiment** (via HF transformers)
* [ ] Extraire les **keywords** et les compter en SQL
* [ ] Dockeriser (service app + DB + LibreTranslate)

---

## Exemple de résultats

<p align="center">
  <img src="outputs/wordcloud_2025-07-23.png" height="200px" />
</p>
