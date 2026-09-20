from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

VerificationStatus = Literal["verified", "partially_verified", "unverified"]
RiskLevel = Literal["low", "medium", "high"]


class DiagnosticRequest(BaseModel):
    linkedin_url: HttpUrl
    subject_name: str = Field(..., min_length=2, max_length=160)
    company_name: str | None = Field(default=None, max_length=160)
    manual_source_urls: list[HttpUrl] = Field(default_factory=list, max_length=12)
    notes: str | None = Field(default=None, max_length=1200)

    @field_validator("linkedin_url")
    @classmethod
    def linkedin_only(cls, value: HttpUrl) -> HttpUrl:
        host = value.host or ""
        if "linkedin.com" not in host.lower():
            raise ValueError("linkedin_url must be a LinkedIn URL")
        return value


class Source(BaseModel):
    url: str
    title: str | None = None
    source_type: str = "web"
    is_primary: bool = False
    snippet: str | None = None
    extracted_text: str | None = None
    error: str | None = None


class Claim(BaseModel):
    text: str
    status: VerificationStatus
    supporting_sources: list[str] = Field(default_factory=list)
    explanation: str


class Gap(BaseModel):
    title: str
    severity: RiskLevel
    evidence: str
    recommendation: str


class RefusedClaim(BaseModel):
    claim: str
    reason: str
    attempted_sources: list[str] = Field(default_factory=list)


class Diagnostic(BaseModel):
    subject_name: str
    company_name: str | None = None
    linkedin_url: str
    executive_summary: str
    findings: list[Claim]
    profile_gaps: list[Gap] = Field(min_length=3, max_length=3)
    refused_claim: RefusedClaim
    source_urls: list[str]
    human_review_required: bool = True
    next_steps: list[str]


class DiagnosticResponse(BaseModel):
    diagnostic: Diagnostic
    sources: list[Source]
    warnings: list[str] = Field(default_factory=list)
