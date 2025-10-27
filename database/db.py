import os
from typing import Optional, Dict
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


class jbdatabase:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.table = "teams"

    def create_team(self, team_name: str) -> Optional[int]:
        # Check if team exists
        res = self.supabase.table(self.table).select("id").eq("team_name", team_name).execute()
        if res.data:
            return res.data[0]["id"]

        # Insert new team
        insert_res = self.supabase.table(self.table).insert({
            "team_name": team_name,
            "overall_time_sec": 0.0,
            "prompt1": None,
            "prompt2": None,
            "prompt3": None,
            "prompt4": None
        }).execute()

        return insert_res.data[0]["id"] if insert_res.data else None

    def addteamsfunc(self, team_name, overall_time_sec, prompt1, prompt2, prompt3, prompt4):
        res = self.supabase.table(self.table).insert({
            "team_name": team_name,
            "overall_time_sec": overall_time_sec,
            "prompt1": prompt1,
            "prompt2": prompt2,
            "prompt3": prompt3,
            "prompt4": prompt4
        }).execute()
        return res.data[0]["id"] if res.data else None

    def update_prompt(self, team_name: str, level: int, prompt_text: str):
        if level not in (1, 2, 3, 4):
            raise ValueError("level must be 1..4")
        col = f"prompt{level}"
        self.supabase.table(self.table).update({col: prompt_text}).eq("team_name", team_name).execute()

    def finalize_team(self, team_name: str, overall_time_sec: float, prompts: Optional[Dict[int, str]] = None):
        update_data = {"overall_time_sec": overall_time_sec}
        if prompts:
            for lvl, text in prompts.items():
                if lvl in (1, 2, 3, 4):
                    update_data[f"prompt{lvl}"] = text
        self.supabase.table(self.table).update(update_data).eq("team_name", team_name).execute()

    def get_team(self, team_name: str):
        res = self.supabase.table(self.table).select("*").eq("team_name", team_name).execute()
        return res.data[0] if res.data else None

    def fuclol(self):
        """Delete all teams."""
        self.supabase.table(self.table).delete().neq("id", 0).execute()
