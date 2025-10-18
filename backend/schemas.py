from pydantic import BaseModel

class AttackRequest(BaseModel):
    team_id: str | None = "anon"
    prompt: str

class SubmitRequest(BaseModel):
    text: str
    team_id: str
