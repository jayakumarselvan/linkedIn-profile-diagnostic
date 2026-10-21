from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.llm import LLMClient
from app.models import DiagnosticRequest, DiagnosticResponse
from app.research import Researcher
from app.verifier import post_verify_diagnostic

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="LinkedIn Profile Diagnostic",
    description="Public-source LinkedIn profile diagnostic with LiteLLM provider abstraction.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/diagnostics", response_model=DiagnosticResponse)
async def create_diagnostic(request: DiagnosticRequest) -> DiagnosticResponse:
    settings = get_settings()
    researcher = Researcher(settings)
    llm = LLMClient(settings)

    sources, warnings = await researcher.collect_sources(request)
    usable_sources = [source for source in sources if source.extracted_text or source.snippet]
    if not usable_sources:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "No usable public evidence was collected.",
                "warnings": warnings,
                "sources": [source.model_dump() for source in sources],
            },
        )

    try:
        diagnostic = await llm.create_diagnostic(request, usable_sources)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    diagnostic = post_verify_diagnostic(diagnostic, usable_sources)
    return DiagnosticResponse(diagnostic=diagnostic, sources=usable_sources, warnings=warnings)
