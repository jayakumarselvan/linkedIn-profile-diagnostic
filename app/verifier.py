from app.models import Claim, Diagnostic, Source


def post_verify_diagnostic(diagnostic: Diagnostic, sources: list[Source]) -> Diagnostic:
    """Downgrade unsupported claims after the LLM responds."""
    source_map = {source.url: source for source in sources}
    source_urls = set(source_map)

    checked_findings: list[Claim] = []
    for finding in diagnostic.findings:
        supported_urls = [url for url in finding.supporting_sources if url in source_urls]
        has_text_source = any(source_map[url].extracted_text for url in supported_urls)
        has_primary = any(source_map[url].is_primary for url in supported_urls)

        status = finding.status
        explanation = finding.explanation
        if status == "verified" and not has_text_source:
            status = "unverified"
            explanation = (
                f"{explanation} Post-check downgrade: no collected source text directly "
                "supports this claim."
            )
        elif status == "verified" and not has_primary and len(supported_urls) < 2:
            status = "partially_verified"
            explanation = (
                f"{explanation} Post-check downgrade: supported by collected evidence, "
                "but not by a primary source or two independent sources."
            )

        checked_findings.append(
            Claim(
                text=finding.text,
                status=status,
                supporting_sources=supported_urls,
                explanation=explanation,
            )
        )

    diagnostic.findings = checked_findings
    diagnostic.source_urls = sorted(source_urls)
    diagnostic.human_review_required = True
    return diagnostic
