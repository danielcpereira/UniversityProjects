"""
Server using FastMCP and REST
Domain: Films + Directors
Exposes: tools (CRUD), resources (2), prompt (1)
Run with: python cinema_server.py
"""

import sqlite3
import os
from fastmcp import FastMCP
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import threading

# DATABASE SETUP 
DB_PATH = "cinema.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS directors (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL UNIQUE,
            country TEXT,
            birth_year INTEGER
        );

        CREATE TABLE IF NOT EXISTS films (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            year        INTEGER,
            genre       TEXT,
            rating      REAL,
            director_id INTEGER REFERENCES directors(id) ON DELETE SET NULL
        );
    """)
    conn.commit()
    conn.close()

init_db()

# FASTMCP 
mcp = FastMCP(name="CinemaServer")

# DIRECTOR TOOLS 

@mcp.tool()
def list_directors() -> str:
    """List all directors in the database."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM directors ORDER BY name").fetchall()
    conn.close()
    if not rows:
        return "No directors found."
    return "\n".join(
        f"[{r['id']}] {r['name']} ({r['country']}, b.{r['birth_year']})"
        for r in rows
    )

@mcp.tool()
def get_director(director_id: int) -> str:
    """Get a director by ID."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM directors WHERE id=?", (director_id,)).fetchone()
    conn.close()
    if not row:
        return f"Error: Director with id={director_id} not found."
    return f"[{row['id']}] {row['name']} | Country: {row['country']} | Born: {row['birth_year']}"

@mcp.tool()
def add_director(name: str, country: str, birth_year: int) -> str:
    """Add a new director. birth_year must be a valid integer year."""
    if birth_year < 1800 or birth_year > 2026:
        # Required: operation that returns an error
        return f"Error: birth_year={birth_year} is out of valid range (1800–2026)."
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO directors (name, country, birth_year) VALUES (?,?,?)",
            (name, country, birth_year)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return f"Director added with id={new_id}: {name} ({country}, b.{birth_year})"
    except sqlite3.IntegrityError:
        conn.close()
        return f"Error: A director named '{name}' already exists."

@mcp.tool()
def add_director_from_string(info_string: str) -> str:
    """
    Add a director from a single formatted string: 'Name | Country | BirthYear'.
    Variation of add_director that accepts and returns strings only.
    Example: 'Stanley Kubrick | American | 1928'
    """
    try:
        parts = [p.strip() for p in info_string.split("|")]
        if len(parts) != 3:
            return "Error: Format must be 'Name | Country | BirthYear'."
        name, country, birth_year_str = parts
        birth_year = int(birth_year_str)
        result = add_director(name, country, birth_year)
        return result
    except ValueError:
        return "Error: BirthYear must be a number. Format: 'Name | Country | BirthYear'."

@mcp.tool()
def update_director(director_id: int, name: str = None, country: str = None, birth_year: int = None) -> str:
    """Update an existing director's fields (only provided fields are updated)."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM directors WHERE id=?", (director_id,)).fetchone()
    if not row:
        conn.close()
        return f"Error: Director with id={director_id} not found."
    new_name       = name       if name       is not None else row["name"]
    new_country    = country    if country    is not None else row["country"]
    new_birth_year = birth_year if birth_year is not None else row["birth_year"]
    conn.execute(
        "UPDATE directors SET name=?, country=?, birth_year=? WHERE id=?",
        (new_name, new_country, new_birth_year, director_id)
    )
    conn.commit()
    conn.close()
    return f"Director id={director_id} updated: {new_name} ({new_country}, b.{new_birth_year})"

@mcp.tool()
def delete_director(director_id: int) -> str:
    """Delete a director by ID. Films by this director will have director_id set to NULL."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM directors WHERE id=?", (director_id,)).fetchone()
    if not row:
        conn.close()
        return f"Error: Director with id={director_id} not found."
    conn.execute("DELETE FROM directors WHERE id=?", (director_id,))
    conn.commit()
    conn.close()
    return f"Director id={director_id} ('{row['name']}') deleted."

# FILM TOOLS 

@mcp.tool()
def list_films() -> str:
    """List all films in the database, including director name."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT f.id, f.title, f.year, f.genre, f.rating, d.name as director
        FROM films f LEFT JOIN directors d ON f.director_id = d.id
        ORDER BY f.year DESC
    """).fetchall()
    conn.close()
    if not rows:
        return "No films found."
    return "\n".join(
        f"[{r['id']}] '{r['title']}' ({r['year']}) | {r['genre']} | ★{r['rating']} | Dir: {r['director'] or 'Unknown'}"
        for r in rows
    )

@mcp.tool()
def get_film(film_id: int) -> str:
    """Get a film by ID."""
    conn = get_conn()
    row = conn.execute("""
        SELECT f.*, d.name as director
        FROM films f LEFT JOIN directors d ON f.director_id = d.id
        WHERE f.id=?
    """, (film_id,)).fetchone()
    conn.close()
    if not row:
        return f"Error: Film with id={film_id} not found."
    return (
        f"[{row['id']}] '{row['title']}' ({row['year']}) | Genre: {row['genre']} | "
        f"Rating: ★{row['rating']} | Director: {row['director'] or 'Unknown'}"
    )

@mcp.tool()
def add_film(title: str, year: int, genre: str, rating: float, director_id: int) -> str:
    """
    Add a new film. rating must be between 0.0 and 10.0.
    director_id must refer to an existing director.
    """
    if not (0.0 <= rating <= 10.0):
        # Required: operation that returns an error 
        return f"Error: rating={rating} must be between 0.0 and 10.0."
    conn = get_conn()
    # Required: operation that raises an exception
    director = conn.execute("SELECT id FROM directors WHERE id=?", (director_id,)).fetchone()
    if not director:
        conn.close()
        raise ValueError(f"Director with id={director_id} does not exist. Add the director first.")
    cur = conn.execute(
        "INSERT INTO films (title, year, genre, rating, director_id) VALUES (?,?,?,?,?)",
        (title, year, genre, rating, director_id)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return f"Film added with id={new_id}: '{title}' ({year}) by director_id={director_id}"

@mcp.tool()
def add_film_from_string(info_string: str) -> str:
    """
    Add a film from a single formatted string: 'Title | Year | Genre | Rating | DirectorId'.
    Variation of add_film that accepts and returns strings only.
    Example: 'Oppenheimer | 2023 | Biography | 8.3 | 1'
    """
    try:
        parts = [p.strip() for p in info_string.split("|")]
        if len(parts) != 5:
            return "Error: Format must be 'Title | Year | Genre | Rating | DirectorId'."
        title, year_str, genre, rating_str, director_id_str = parts
        result = add_film(title, int(year_str), genre, float(rating_str), int(director_id_str))
        return result
    except ValueError as e:
        return f"Error: {e}"

@mcp.tool()
def update_film(film_id: int, title: str = None, year: int = None, genre: str = None,
                rating: float = None, director_id: int = None) -> str:
    """Update an existing film (only provided fields are changed)."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM films WHERE id=?", (film_id,)).fetchone()
    if not row:
        conn.close()
        return f"Error: Film with id={film_id} not found."
    conn.execute("""
        UPDATE films SET title=?, year=?, genre=?, rating=?, director_id=? WHERE id=?
    """, (
        title       if title       is not None else row["title"],
        year        if year        is not None else row["year"],
        genre       if genre       is not None else row["genre"],
        rating      if rating      is not None else row["rating"],
        director_id if director_id is not None else row["director_id"],
        film_id
    ))
    conn.commit()
    conn.close()
    return f"Film id={film_id} updated successfully."

@mcp.tool()
def delete_film(film_id: int) -> str:
    """Delete a film by ID."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM films WHERE id=?", (film_id,)).fetchone()
    if not row:
        conn.close()
        return f"Error: Film with id={film_id} not found."
    conn.execute("DELETE FROM films WHERE id=?", (film_id,))
    conn.commit()
    conn.close()
    return f"Film id={film_id} ('{row['title']}') deleted."

@mcp.tool()
def films_by_director(director_id: int) -> str:
    """
    List all films by a specific director.
    director_id must be a valid integer ID from the directors table.
    Use list_directors first to find the correct director_id.
    """
    conn = get_conn()
    director = conn.execute("SELECT name FROM directors WHERE id=?", (director_id,)).fetchone()
    if not director:
        conn.close()
        return f"Error: Director with id={director_id} not found."
    rows = conn.execute(
        "SELECT * FROM films WHERE director_id=? ORDER BY year", (director_id,)
    ).fetchall()
    conn.close()
    if not rows:
        return f"No films found for director '{director['name']}'."
    return f"Films by {director['name']}:\n" + "\n".join(
        f"  [{r['id']}] '{r['title']}' ({r['year']}) ★{r['rating']}" for r in rows
    )

# RESOURCES 

@mcp.resource("info://cinema-server")
def get_server_info() -> str:
    """General information about this Cinema MCP server."""
    return (
        "CinemaServer v1.0\n"
        "Domain: Films and Directors\n"
        "Purpose: Manage a cinema catalogue via MCP tools and REST API.\n"
        "Entities: Director (id, name, country, birth_year), Film (id, title, year, genre, rating, director_id)\n"
        "Available tools: list_directors, get_director, add_director, add_director_from_string, "
        "update_director, delete_director, list_films, get_film, add_film, add_film_from_string, "
        "update_film, delete_film, films_by_director\n"
        "Built with: FastMCP + Python + SQLite\n"
    )

@mcp.resource("info://cinema-schema")
def get_schema_info() -> str:
    """Returns the database schema and data model for the Cinema server."""
    return """
DATABASE SCHEMA — cinema.db
============================

TABLE: directors
  id         INTEGER  PRIMARY KEY AUTOINCREMENT
  name       TEXT     NOT NULL UNIQUE
  country    TEXT
  birth_year INTEGER

TABLE: films
  id          INTEGER  PRIMARY KEY AUTOINCREMENT
  title       TEXT     NOT NULL
  year        INTEGER
  genre       TEXT
  rating      REAL     (0.0 – 10.0)
  director_id INTEGER  REFERENCES directors(id) ON DELETE SET NULL

RELATIONSHIPS:
  One Director → Many Films (one-to-many)
  A Film can have NULL director_id if the director is deleted

NOTES:
  - add_film raises an exception if director_id does not exist
  - add_film returns an error string if rating is out of range
  - add_director returns an error string if birth_year is out of range
  - add_director_from_string and add_film_from_string accept pipe-delimited strings
"""

# PROMPT 

@mcp.prompt()
def cinema_assistant_prompt(user_name: str = "User") -> str:
    """System prompt that turns the LLM into a cinema assistant."""
    return (
        f"You are CineGPT, a knowledgeable and enthusiastic cinema assistant. "
        f"You are currently helping {user_name}. "
        "You manage a catalogue of Films and Directors stored in a database. "
        "You can list, add, update, and delete both directors and films using your tools. "
        "When adding a film, always verify the director exists first. "
        "When a tool returns an error message (starting with 'Error:'), explain it clearly to the user and suggest a fix. "
        "If a tool raises an exception (e.g. director not found), apologise and guide the user to resolve it. "
        "Keep your tone friendly, concise, and passionate about cinema. "
        "Always present lists in a readable format. "
        "You are NOT a general AI — stay focused on the cinema domain."
    )

# REST API -----------------------------------

rest_app = FastAPI(title="Cinema REST API")
rest_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class DirectorIn(BaseModel):
    name: str
    country: Optional[str] = None
    birth_year: Optional[int] = None

class FilmIn(BaseModel):
    title: str
    year: Optional[int] = None
    genre: Optional[str] = None
    rating: Optional[float] = None
    director_id: Optional[int] = None

# Directors REST
@rest_app.get("/directors")
def rest_list_directors():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM directors ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@rest_app.get("/directors/{director_id}")
def rest_get_director(director_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM directors WHERE id=?", (director_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Director not found")
    return dict(row)

@rest_app.post("/directors", status_code=201)
def rest_add_director(body: DirectorIn):
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO directors (name, country, birth_year) VALUES (?,?,?)",
            (body.name, body.country, body.birth_year)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return {"id": new_id, **body.dict()}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail=f"Director '{body.name}' already exists")

@rest_app.put("/directors/{director_id}")
def rest_update_director(director_id: int, body: DirectorIn):
    conn = get_conn()
    row = conn.execute("SELECT * FROM directors WHERE id=?", (director_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Director not found")
    conn.execute("UPDATE directors SET name=?, country=?, birth_year=? WHERE id=?",
                 (body.name or row["name"], body.country or row["country"], body.birth_year or row["birth_year"], director_id))
    conn.commit()
    conn.close()
    return {"id": director_id, **body.dict()}

@rest_app.delete("/directors/{director_id}")
def rest_delete_director(director_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM directors WHERE id=?", (director_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Director not found")
    conn.execute("DELETE FROM directors WHERE id=?", (director_id,))
    conn.commit()
    conn.close()
    return {"deleted": director_id}

# Films REST
@rest_app.get("/films")
def rest_list_films():
    conn = get_conn()
    rows = conn.execute("""
        SELECT f.*, d.name as director_name FROM films f
        LEFT JOIN directors d ON f.director_id = d.id ORDER BY f.year DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@rest_app.get("/films/{film_id}")
def rest_get_film(film_id: int):
    conn = get_conn()
    row = conn.execute("""
        SELECT f.*, d.name as director_name FROM films f
        LEFT JOIN directors d ON f.director_id = d.id WHERE f.id=?
    """, (film_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Film not found")
    return dict(row)

@rest_app.post("/films", status_code=201)
def rest_add_film(body: FilmIn):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO films (title, year, genre, rating, director_id) VALUES (?,?,?,?,?)",
        (body.title, body.year, body.genre, body.rating, body.director_id)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, **body.dict()}

@rest_app.put("/films/{film_id}")
def rest_update_film(film_id: int, body: FilmIn):
    conn = get_conn()
    row = conn.execute("SELECT * FROM films WHERE id=?", (film_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Film not found")
    conn.execute("UPDATE films SET title=?, year=?, genre=?, rating=?, director_id=? WHERE id=?",
                 (body.title or row["title"], body.year or row["year"], body.genre or row["genre"],
                  body.rating or row["rating"], body.director_id or row["director_id"], film_id))
    conn.commit()
    conn.close()
    return {"id": film_id, **body.dict()}

@rest_app.delete("/films/{film_id}")
def rest_delete_film(film_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM films WHERE id=?", (film_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Film not found")
    conn.execute("DELETE FROM films WHERE id=?", (film_id,))
    conn.commit()
    conn.close()
    return {"deleted": film_id}

@rest_app.get("/health")
def rest_health():
    return {"status": "ok"}

# ENTRY POINT 
if __name__ == "__main__":
    # REST API on port 8001 in a background thread
    def run_rest():
        uvicorn.run(rest_app, host="127.0.0.1", port=8001, log_level="warning")

    t = threading.Thread(target=run_rest, daemon=True)
    t.start()
    print("🎬 REST API running on http://127.0.0.1:8001")
    print("🎬 MCP  SSE  running on http://127.0.0.1:8002/sse")

    # MCP Server on port 8002
    mcp.run(transport="sse", host="127.0.0.1", port=8002)