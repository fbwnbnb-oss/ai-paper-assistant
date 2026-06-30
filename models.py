import sqlite3
import os
from datetime import datetime, date
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papers.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                arxiv_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                summary TEXT NOT NULL,
                categories TEXT NOT NULL,
                published TEXT NOT NULL,
                pdf_url TEXT NOT NULL,
                fetched_date TEXT NOT NULL,
                relevance_score INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS paper_status (
                arxiv_id TEXT PRIMARY KEY,
                is_read INTEGER DEFAULT 0,
                is_favorite INTEGER DEFAULT 0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
            )
        """)

def save_paper(paper: dict, fetched_date: str):
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO papers
            (arxiv_id, title, authors, summary, categories, published, pdf_url, fetched_date, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper['arxiv_id'],
            paper['title'],
            paper['authors'],
            paper['summary'],
            paper['categories'],
            paper['published'],
            paper['pdf_url'],
            fetched_date,
            paper['relevance_score']
        ))

def get_papers_by_date(target_date: str):
    with get_db() as conn:
        papers = conn.execute("""
            SELECT p.*,
                   COALESCE(ps.is_read, 0) as is_read,
                   COALESCE(ps.is_favorite, 0) as is_favorite
            FROM papers p
            LEFT JOIN paper_status ps ON p.arxiv_id = ps.arxiv_id
            WHERE p.fetched_date = ?
            ORDER BY p.relevance_score DESC, p.published DESC
        """, (target_date,)).fetchall()
        return [dict(row) for row in papers]

def get_all_dates():
    with get_db() as conn:
        dates = conn.execute("""
            SELECT DISTINCT fetched_date
            FROM papers
            ORDER BY fetched_date DESC
        """).fetchall()
        return [row['fetched_date'] for row in dates]

def update_paper_status(arxiv_id: str, is_read: bool = None, is_favorite: bool = None):
    with get_db() as conn:
        now = datetime.now().isoformat()

        existing = conn.execute(
            "SELECT * FROM paper_status WHERE arxiv_id = ?",
            (arxiv_id,)
        ).fetchone()

        if existing:
            updates = []
            params = []
            if is_read is not None:
                updates.append("is_read = ?")
                params.append(1 if is_read else 0)
            if is_favorite is not None:
                updates.append("is_favorite = ?")
                params.append(1 if is_favorite else 0)

            if updates:
                updates.append("updated_at = ?")
                params.append(now)
                params.append(arxiv_id)
                conn.execute(
                    f"UPDATE paper_status SET {', '.join(updates)} WHERE arxiv_id = ?",
                    params
                )
        else:
            conn.execute("""
                INSERT INTO paper_status (arxiv_id, is_read, is_favorite, updated_at)
                VALUES (?, ?, ?, ?)
            """, (arxiv_id, 1 if is_read else 0, 1 if is_favorite else 0, now))

def paper_exists(arxiv_id: str):
    with get_db() as conn:
        return conn.execute(
            "SELECT 1 FROM papers WHERE arxiv_id = ?",
            (arxiv_id,)
        ).fetchone() is not None
