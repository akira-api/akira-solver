from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

from core.queue import solver_queue
from models.request import SolveRequest
from models.response import SolveResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/solve", response_model=SolveResponse)
async def solve_endpoint(request: SolveRequest) -> JSONResponse:
    logger.info("Received solve request for URL: %s", request.url)
    cookie_string, solve_seconds = await solver_queue.submit(request.url)
    return JSONResponse(content={
        "cookies": cookie_string,
        "solve_seconds": solve_seconds,
    })