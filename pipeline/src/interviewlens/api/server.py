"""Minimal FastAPI wrapper around the pipeline — Person D.

Run with: uvicorn interviewlens.api.server:app --reload
"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from pydantic import BaseModel

from interviewlens.orchestration.pipeline import run_pipeline

app = FastAPI(title="InterviewLens API")


class AnalyzeRequest(BaseModel):
    question: str


@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    report = run_pipeline(req.question)
    return asdict(report)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
