CREATE TABLE IF NOT EXISTS articles_fr (
    id SERIAL PRIMARY KEY,
    title TEXT,
    url TEXT UNIQUE,
    source TEXT,
    category TEXT,
    published_at TIMESTAMP,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
