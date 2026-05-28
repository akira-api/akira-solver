from pydantic import BaseModel


class SolveResponse(BaseModel):
    cookies: str
    solve_seconds: float