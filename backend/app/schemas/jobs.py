from pydantic import BaseModel

class CreateJobRequest(BaseModel):
    job_type: str
    payload: dict

class JobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    payload: dict
    result: dict | None = None
    error: str | None = None
