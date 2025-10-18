import sqlite3
from contextlib import contextmanager

class JailbreakDatabase:
    def __init__(self, db_path: str = "jailbreak.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def getconnections(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
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
    
    def addteamsfunc(self, team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4):
        with self.getconnections() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO teams (team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4))
            return cursor.lastrowid
    
    def fuclol(self): #clears table 
        with self.getconnections() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM teams')
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="teams"')
