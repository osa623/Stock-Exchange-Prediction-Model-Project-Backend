from fastapi import APIRouter

router = APIRouter()

@router.get("/disabled")
def disabled():
    return {"message": "Jobs are not part of this architecture"}
