"""WLVCPP API — cell-penetrating peptide prediction.

POST /api/predict  { "fasta": ">name\\nSEQUENCE\\n..." }  -> predictions + discarded entries
GET  /api/health
"""
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from wlvcpp.parse import check_entries
from wlvcpp.predict import predict_peptides, residue_groups
from auth import BasicAuthMiddleware

app = FastAPI(title="WLVCPP API", version="1.0.0")

app.add_middleware(BasicAuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your real frontend origin(s) in production
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_ENTRIES_PER_REQUEST = 500  # guard against oversized pastes


class PredictRequest(BaseModel):
    fasta: str


class PredictionOut(BaseModel):
    name: str
    peptide: str
    predicted_class: str
    probability: float
    residue_groups: List[str]


class DiscardedOut(BaseModel):
    line: str
    content: str


class PredictResponse(BaseModel):
    predictions: List[PredictionOut]
    discarded: List[DiscardedOut]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    fasta = req.fasta.strip()
    if not fasta:
        raise HTTPException(status_code=400, detail="No sequence data provided.")

    lines = fasta.splitlines()
    names, peps, nonalphabetic = check_entries(lines)

    if len(peps) > MAX_ENTRIES_PER_REQUEST:
        raise HTTPException(
            status_code=413,
            detail=f"Too many entries ({len(peps)}). Max {MAX_ENTRIES_PER_REQUEST} per request.",
        )

    if not peps:
        raise HTTPException(
            status_code=422,
            detail="No valid peptide entries found. Check FASTA formatting.",
        )

    try:
        results = predict_peptides(names, peps)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    predictions = [
        PredictionOut(**r, residue_groups=residue_groups(r["peptide"]))
        for r in results
    ]
    discarded = [DiscardedOut(line=d[0], content=d[1]) for d in nonalphabetic]

    return PredictResponse(predictions=predictions, discarded=discarded)


# Serve the built Vue frontend (if present) at /
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except RuntimeError:
    pass  # static/ not built yet — fine for local API-only dev
