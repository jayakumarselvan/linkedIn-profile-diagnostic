from app.models import Claim, Diagnostic, Gap, RefusedClaim, Source
from app.verifier import post_verify_diagnostic


def make_diagnostic(claim: Claim) -> Diagnostic:
    return Diagnostic(
        subject_name="Jane Founder",
        company_name="Example Capital",
        linkedin_url="https://www.linkedin.com/in/jane",
        executive_summary="Summary",
        findings=[claim],
        profile_gaps=[
            Gap(title="Gap 1", severity="medium", evidence="Evidence", recommendation="Fix"),
            Gap(title="Gap 2", severity="medium", evidence="Evidence", recommendation="Fix"),
            Gap(title="Gap 3", severity="medium", evidence="Evidence", recommendation="Fix"),
        ],
        refused_claim=RefusedClaim(claim="Raised $10M", reason="No source"),
        source_urls=[],
        next_steps=["Review"],
    )


def test_verified_claim_without_source_text_is_downgraded() -> None:
    diagnostic = make_diagnostic(
        Claim(
            text="Jane founded Example Capital.",
            status="verified",
            supporting_sources=["https://example.com/about"],
            explanation="Supported.",
        )
    )
    source = Source(url="https://example.com/about", title="About", extracted_text=None)

    checked = post_verify_diagnostic(diagnostic, [source])

    assert checked.findings[0].status == "unverified"


def test_verified_non_primary_single_source_is_partially_verified() -> None:
    diagnostic = make_diagnostic(
        Claim(
            text="Jane founded Example Capital.",
            status="verified",
            supporting_sources=["https://news.example/story"],
            explanation="Supported.",
        )
    )
    source = Source(
        url="https://news.example/story",
        title="Story",
        extracted_text="Jane founded Example Capital.",
        is_primary=False,
    )

    checked = post_verify_diagnostic(diagnostic, [source])

    assert checked.findings[0].status == "partially_verified"
