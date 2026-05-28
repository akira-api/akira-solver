from pydantic import BaseModel


class SolveRequest(BaseModel):
    url: str