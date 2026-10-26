from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(include_in_schema=False)


@router.get("/", summary="Redirect to Swagger")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")
