from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from .webrtc import handle_offer

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", "r", encoding='utf-8') as f:
        content = f.read()
    return HTMLResponse(content=content)

@router.post("/offer")
async def offer(request: Request):
    return await handle_offer(request)

