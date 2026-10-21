import json

from litellm import acompletion
from pydantic import ValidationError

from app.config import Settings
from app.models import Diagnostic, DiagnosticRequest, Source

SYSTEM_PROMPT = """You are an evidence-first analyst for a reputation advisory.
You must not invent facts. Use only the supplied public-source evidence.
Any uncertain factual claim must be labelled partially_verified or unverified.
Do not use hashtags, em dashes, or generic AI filler language.
Return strict JSON matching the requested schema."""


def build_user_prompt(request: DiagnosticRequest, sources: list[Source]) -> str:
    source_blocks = []
    for index, source in enumerate(sources, start=1):
        text = source.extracted_text or source.snippet or source.error or ""
        source_blocks.append(
            "\n".join(
                [
                    f"[{index}] {source.title or 'Untitled'}",
                    f"url: {source.url}",
                    f"primary_source_guess: {source.is_primary}",
                    f"text: {text[:4500]}",
                ]
            )
        )

    return f"""
Create a one-page diagnostic for Track B.

Subject name: {request.subject_name}
Company: {request.company_name or "Unknown"}
LinkedIn URL: {request.linkedin_url}
User notes: {request.notes or "None"}

Evidence:
{chr(10).join(source_blocks) or "No source text was collected."}

Return JSON with exactly this shape:
{{
  "subject_name": "...",
  "company_name": "... or null",
  "linkedin_url": "...",
  "executive_summary": "short, concrete summary",
  "findings": [
    {{
      "text": "single factual finding",
      "status": "verified | partially_verified | unverified",
      "supporting_sources": ["source URLs"],
      "explanation": "why this label is justified"
    }}
  ],
  "profile_gaps": [
    {{
      "title": "gap title",
      "severity": "low | medium | high",
      "evidence": "what in the evidence shows this gap",
      "recommendation": "specific next action"
    }}
  ],
  "refused_claim": {{
    "claim": "a claim that should not be included",
    "reason": "why evidence is insufficient",
    "attempted_sources": ["source URLs checked"]
  }},
  "source_urls": ["all useful source URLs"],
  "human_review_required": true,
  "next_steps": ["specific next step"]
}}

Rules:
- Include exactly 3 profile_gaps.
- Do not include a factual finding as verified unless at least one source directly supports it.
- Prefer primary sources for verified claims.
- Include at least one refused claim, even if it is a tempting but unsupported inference.
- Keep output suitable for a DIFC-facing advisor.
"""


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def create_diagnostic(
        self, request: DiagnosticRequest, sources: list[Source]
    ) -> Diagnostic:
        response = await acompletion(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(request, sources)},
            ],
            temperature=self.settings.llm_temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned an empty response")
        try:
            return Diagnostic.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"LLM returned invalid diagnostic JSON: {exc}") from exc
