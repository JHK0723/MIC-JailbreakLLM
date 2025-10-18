CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name TEXT UNIQUE NOT NULL,
    overall_time_sec REAL NOT NULL,
    prompt1 TEXT,
    prompt2 TEXT,
    prompt3 TEXT,
    prompt4 TEXT
);
