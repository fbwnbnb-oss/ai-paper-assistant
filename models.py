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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arxiv_id TEXT UNIQUE NOT NULL,
                full_text TEXT,
                translated_text TEXT,
                summary TEXT,
                studied_at TEXT NOT NULL,
                FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS opensource_projects (
                repo_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT NOT NULL,
                org TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL,
                stars INTEGER DEFAULT 0,
                language TEXT,
                topics TEXT,
                created_at TEXT,
                updated_at TEXT,
                fetched_date TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS opensource_status (
                repo_id TEXT PRIMARY KEY,
                is_read INTEGER DEFAULT 0,
                is_favorite INTEGER DEFAULT 0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (repo_id) REFERENCES opensource_projects(repo_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS view_history (
                arxiv_id TEXT PRIMARY KEY,
                viewed_at TEXT NOT NULL,
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


def init_study_table():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arxiv_id TEXT UNIQUE NOT NULL,
                full_text TEXT,
                translated_text TEXT,
                summary TEXT,
                studied_at TEXT NOT NULL,
                FOREIGN KEY (arxiv_id) REFERENCES papers(arxiv_id)
            )
        """)


def get_study_record(arxiv_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM study_records WHERE arxiv_id = ?",
            (arxiv_id,)
        ).fetchone()
        return dict(row) if row else None


def save_study_record(arxiv_id: str, full_text: str, translated_text: str, summary: str):
    with get_db() as conn:
        now = datetime.now().isoformat()
        conn.execute("""
            INSERT INTO study_records (arxiv_id, full_text, translated_text, summary, studied_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(arxiv_id) DO UPDATE SET
                full_text = excluded.full_text,
                translated_text = excluded.translated_text,
                summary = excluded.summary,
                studied_at = excluded.studied_at
        """, (arxiv_id, full_text, translated_text, summary, now))


def get_study_history():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT sr.arxiv_id, sr.summary, sr.studied_at, p.title, p.categories
            FROM study_records sr
            JOIN papers p ON sr.arxiv_id = p.arxiv_id
            ORDER BY sr.studied_at DESC
        """).fetchall()
        return [dict(row) for row in rows]


def save_opensource_project(project: dict, fetched_date: str):
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO opensource_projects
            (repo_id, name, company, org, description, url, stars, language, topics, created_at, updated_at, fetched_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project['repo_id'], project['name'], project['company'], project['org'],
            project['description'], project['url'], project['stars'], project['language'],
            project['topics'], project['created_at'], project['updated_at'], fetched_date
        ))


def get_opensource_projects(company=None, target_date=None):
    with get_db() as conn:
        conditions = []
        params = []
        if company and company != 'all':
            conditions.append("op.company = ?")
            params.append(company)
        if target_date:
            conditions.append("op.fetched_date = ?")
            params.append(target_date)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = conn.execute(f"""
            SELECT op.*, COALESCE(os.is_read, 0) as is_read, COALESCE(os.is_favorite, 0) as is_favorite
            FROM opensource_projects op
            LEFT JOIN opensource_status os ON op.repo_id = os.repo_id
            {where}
            ORDER BY op.stars DESC
        """, params).fetchall()
        return [dict(row) for row in rows]


def get_opensource_dates():
    with get_db() as conn:
        dates = conn.execute("""
            SELECT DISTINCT fetched_date FROM opensource_projects ORDER BY fetched_date DESC
        """).fetchall()
        return [row['fetched_date'] for row in dates]


def update_opensource_status(repo_id: str, is_read: bool = None, is_favorite: bool = None):
    with get_db() as conn:
        now = datetime.now().isoformat()
        existing = conn.execute(
            "SELECT * FROM opensource_status WHERE repo_id = ?", (repo_id,)
        ).fetchone()

        if existing:
            updates, params = [], []
            if is_read is not None:
                updates.append("is_read = ?")
                params.append(1 if is_read else 0)
            if is_favorite is not None:
                updates.append("is_favorite = ?")
                params.append(1 if is_favorite else 0)
            if updates:
                updates.append("updated_at = ?")
                params.append(now)
                params.append(repo_id)
                conn.execute(f"UPDATE opensource_status SET {', '.join(updates)} WHERE repo_id = ?", params)
        else:
            conn.execute("""
                INSERT INTO opensource_status (repo_id, is_read, is_favorite, updated_at)
                VALUES (?, ?, ?, ?)
            """, (repo_id, 1 if is_read else 0, 1 if is_favorite else 0, now))


def record_view(arxiv_id: str):
    with get_db() as conn:
        now = datetime.now().isoformat()
        conn.execute("""
            INSERT INTO view_history (arxiv_id, viewed_at) VALUES (?, ?)
            ON CONFLICT(arxiv_id) DO UPDATE SET viewed_at = excluded.viewed_at
        """, (arxiv_id, now))


def get_view_history():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT p.*, vh.viewed_at,
                   COALESCE(ps.is_read, 0) as is_read,
                   COALESCE(ps.is_favorite, 0) as is_favorite
            FROM view_history vh
            JOIN papers p ON vh.arxiv_id = p.arxiv_id
            LEFT JOIN paper_status ps ON p.arxiv_id = ps.arxiv_id
            ORDER BY vh.viewed_at DESC
        """).fetchall()
        return [dict(row) for row in rows]
