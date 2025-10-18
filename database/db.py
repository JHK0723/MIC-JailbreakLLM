import sqlite3
from contextlib import contextmanager

class jbdatabase:
    def __init__(self, db_path: str = "jailbreak.db"):
        self.db_path = db_path  # store path
        self.init_database()  # setup schema
    
    @contextmanager
    def getconnections(self):
        conn = sqlite3.connect(self.db_path)  # connect db
        conn.row_factory = sqlite3.Row  # dict results
        try:
            yield conn  
            conn.commit()  # save changes
        except Exception as e:
            conn.rollback() 
            raise e
        finally:
            conn.close() 
    
    def init_database(self):
      
        with self.getconnections() as conn:  # get connection
            cursor = conn.cursor()  # get cursor
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
       
        with self.getconnections() as conn:  # get connection
            cursor = conn.cursor()  # get cursor
            cursor.execute('''
                INSERT INTO teams (team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4))  
            return cursor.lastrowid  # return id-> lastrowid, returns the primary key
    
    def fuclol(self):# clear table
        with self.getconnections() as conn:  
            cursor = conn.cursor()  
            cursor.execute('DELETE FROM teams') 
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="teams"')
