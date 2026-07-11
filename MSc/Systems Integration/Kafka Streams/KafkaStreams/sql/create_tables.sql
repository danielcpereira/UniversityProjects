-- ============================================================
-- Cinema Streaming Platform - Database Schema
-- ============================================================

-- Genres
CREATE TABLE IF NOT EXISTS genres (
    genre_id   SERIAL PRIMARY KEY,
    genre_name VARCHAR(60) NOT NULL UNIQUE
);

INSERT INTO genres (genre_name) VALUES
    ('Action'), ('Drama'), ('Comedy'), ('Thriller'),
    ('Science Fiction'), ('Horror'), ('Animation'), ('Documentary')
ON CONFLICT DO NOTHING;

-- Films
CREATE TABLE IF NOT EXISTS films (
    film_id         SERIAL PRIMARY KEY,
    title           VARCHAR(120) NOT NULL UNIQUE,
    genre_id        INTEGER NOT NULL REFERENCES genres(genre_id),
    base_price      NUMERIC(8,2) NOT NULL
);

INSERT INTO films (title, genre_id, base_price) VALUES
    ('Galactic Odyssey',     5, 14.99),
    ('Shadow Protocol',      4, 12.99),
    ('Laugh Factory',        3,  9.99),
    ('The Last Frontier',    1, 11.99),
    ('Silent Waters',        2, 13.99),
    ('Night Crawler',        6, 10.99),
    ('Tiny Heroes',          7,  8.99),
    ('Planet in Peril',      8, 12.49)
ON CONFLICT DO NOTHING;

-- ============================================================
-- Results tables — nomes iguais aos Kafka topics
-- ============================================================

CREATE TABLE IF NOT EXISTS "CinemaRevenuePerFilm" (
    id       VARCHAR(120) PRIMARY KEY,
    revenue  NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaExpensesPerFilm" (
    id       VARCHAR(120) PRIMARY KEY,
    expenses NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaProfitPerFilm" (
    id     VARCHAR(120) PRIMARY KEY,
    profit NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaTotalRevenue" (
    id      VARCHAR(10) PRIMARY KEY,
    revenue NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaTotalExpenses" (
    id       VARCHAR(10) PRIMARY KEY,
    expenses NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaTotalProfit" (
    id     VARCHAR(10) PRIMARY KEY,
    profit NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaAvgTransactionPerFilm" (
    id        VARCHAR(120) PRIMARY KEY,
    avg_value NUMERIC(12,4),
    count     BIGINT
);

CREATE TABLE IF NOT EXISTS "CinemaAvgTransactionAllFilms" (
    id        VARCHAR(10) PRIMARY KEY,
    avg_value NUMERIC(12,4),
    count     BIGINT
);

CREATE TABLE IF NOT EXISTS "CinemaHighestProfitFilm" (
    id         VARCHAR(10) PRIMARY KEY,
    film_title VARCHAR(120),
    profit     NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaRevenueLastHour" (
    id      VARCHAR(40) PRIMARY KEY,
    revenue NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaExpensesLastHour" (
    id       VARCHAR(40) PRIMARY KEY,
    expenses NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaProfitLastHour" (
    id     VARCHAR(40) PRIMARY KEY,
    profit NUMERIC(12,4)
);

CREATE TABLE IF NOT EXISTS "CinemaTopGenrePerFilm" (
    id         VARCHAR(120) PRIMARY KEY,
    genre_name VARCHAR(60),
    revenue    NUMERIC(12,4)
);