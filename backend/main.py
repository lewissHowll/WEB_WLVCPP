"""WLVCPP API — cell-penetrating peptide prediction.

POST /api/predict  { "fasta": ">name\\nSEQUENCE\\n..." }  -> predictions + discarded entries
POST /api/contact  { "name", "email", "subject", "comment" }  -> emails the site owner
GET  /api/health
"""
from typing import List
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr

from wlvcpp.parse import check_entries
from wlvcpp.predict import predict_peptides, residue_groups
from auth import BasicAuthMiddleware
from mailer import send_contact_email

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


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    comment: str


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


@app.post("/api/contact")
def contact(req: ContactRequest):
    name = req.name.strip()
    subject = req.subject.strip()
    comment = req.comment.strip()

    if not name or not subject or not comment:
        raise HTTPException(status_code=400, detail="Name, subject and message are all required.")
    if len(comment) > 5000:
        raise HTTPException(status_code=400, detail="Message is too long (max 5000 characters).")

    try:
        send_contact_email(name, req.email, subject, comment)
    except RuntimeError as exc:
        # SMTP not configured — fail loudly rather than silently dropping the message
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Failed to send message: {exc}") from exc

    return {"status": "sent"}


# --- Serve the built Vue frontend ---
# Mounting StaticFiles at "/" only serves index.html for the exact root path,
# not for client-side routes like /contact — a hard refresh or direct link to
# /contact would 404. So: serve /assets (JS/CSS) and known static files
# directly, and fall back to index.html for anything else that isn't /api/*,
# letting vue-router's client-side routing take over.
STATIC_DIR = "static"

if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        requested = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(requested):
            return FileResponse(requested)
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Not Found")
