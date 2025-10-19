import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, Dict
from datetime import datetime

DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, "jailbreak.db")


class jbdatabase:
    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def getconnections(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_database(self):
        with self.getconnections() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_name TEXT UNIQUE NOT NULL,
                    overall_time_sec REAL NOT NULL,
                    prompt1 TEXT,
                    prompt2 TEXT,
                    prompt3 TEXT,
                    prompt4 TEXT
                )
            ''')
            # seed default testing team "JHK" if not present
            cursor.execute('SELECT id FROM teams WHERE team_name = ?', ("JHK",))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO teams (team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ("JHK", 0.0, None, None, None, None))

    def addteamsfunc(self, team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4):
        with self.getconnections() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO teams (team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4))
            return cursor.lastrowid

    def fuclol(self):
        with self.getconnections() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM teams')
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="teams"')

    # Primary helpers (no separate prompts table; prompt1..prompt4 hold last saved prompt)
    def create_team(self, team_name: str) -> Optional[int]:
        with self.getconnections() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM teams WHERE team_name = ?', (team_name,))
            row = cursor.fetchone()
            if row:
                return int(row['id'])
            cursor.execute('''
                INSERT INTO teams (team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (team_name, 0.0, None, None, None, None))
            return cursor.lastrowid

    def update_prompt(self, team_name: str, level: int, prompt_text: str):
        """Save the latest prompt that led to an attempt for a given level into prompt{n}."""
        if level not in (1, 2, 3, 4):
            raise ValueError("level must be 1..4")
        col = f"prompt{level}"
        with self.getconnections() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE teams SET {col} = ? WHERE team_name = ?', (prompt_text, team_name))

    def finalize_team(self, team_name: str, overall_time_sec: float, prompts: Optional[Dict[int, str]] = None):
        """Write overall_time_sec and optionally set final prompt snapshots."""
        with self.getconnections() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE teams SET overall_time_sec = ? WHERE team_name = ?', (overall_time_sec, team_name))
            if prompts:
                for lvl, text in prompts.items():
                    if lvl in (1, 2, 3, 4):
                        col = f"prompt{lvl}"
                        cursor.execute(f'UPDATE teams SET {col} = ? WHERE team_name = ?', (text, team_name))

    def get_team(self, team_name: str):
        with self.getconnections() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM teams WHERE team_name = ?', (team_name,))
            row = cursor.fetchone()
            return dict(row) if row else None