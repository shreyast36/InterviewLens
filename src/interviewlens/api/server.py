"""Minimal FastAPI wrapper around the pipeline — Person D.

Run with: uvicorn interviewlens.api.server:app --reload
"""
from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from interviewlens.orchestration.pipeline import run_pipeline, run_pipeline_from_video

logger = logging.getLogger(__name__)

app = FastAPI(title="InterviewLens API")

ALLOWED_VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500MB -- generous for a several-minute interview clip


class AnalyzeRequest(BaseModel):
    question: str


@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    report = run_pipeline(req.question)
    return asdict(report)


@app.post("/analyze_video")
async def analyze_video(question: str = Form(...), video: UploadFile = File(...)) -> dict:
    """Real "user uploads a video" path: runs Pipeline A (pose) -> Pipeline B
    (background) -> A/B fusion -> VLM reasoning -> validation -> coaching report
    against the uploaded file. See orchestration.pipeline.run_pipeline_from_video
    for what's real here vs. still-placeholder (audio is synthetic; there is no
    manual skeleton-review step -- confidence gating substitutes for it).
    """
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in ALLOWED_VIDEO_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video type {suffix!r}. Allowed: {sorted(ALLOWED_VIDEO_SUFFIXES)}",
        )

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            size = 0
            while chunk := await video.read(1 << 20):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Video exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB upload limit.",
                    )
                tmp.write(chunk)

        if size == 0:
            raise HTTPException(status_code=400, detail="Uploaded video is empty.")

        report = run_pipeline_from_video(tmp_path, question)
        return asdict(report)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 -- boundary handler: never leak a raw 500 traceback to the client
        logger.exception("analyze_video failed for %r", video.filename)
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {exc}") from exc
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
