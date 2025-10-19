from pydantic import BaseModel, Field

class SubmitRequest(BaseModel):
    team_id: str = Field(..., description="Team identifier")
    level: int = Field(..., ge=1, le=4, description="Level number (1-4)")
    text: str = Field(..., min_length=1, description="Prompt to attempt jailbreak")

class ValidateRequest(BaseModel):
    team_id: str = Field(..., description="Team identifier")
    level: int = Field(..., ge=1, le=4, description="Level to validate")
    password: str = Field(..., min_length=1, description="Password attempt")