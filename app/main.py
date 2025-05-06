from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vmf import generate_trend_report
from vmf.models import TrendReport

app = FastAPI(title="Video Brief Generator")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # narrow later
    allow_methods=["POST"],
    allow_headers=["*"],
)

class RequestBody(BaseModel):
    song: str | None = None
    artist: str | None = None

@app.post("/generate", response_model=TrendReport)
def generate(body: RequestBody):
    try:
        return generate_trend_report(song=body.song, artist=body.artist)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten later
    allow_methods=["POST"],
    allow_headers=["*"],
)
