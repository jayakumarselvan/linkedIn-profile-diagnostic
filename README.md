# LinkedIn Profile Diagnostic

FastAPI implementation for the LinkedIn Profile Diagnostic.

It starts from a LinkedIn URL, gathers public-source evidence, asks an LLM through
LiteLLM to produce a one-page LinkedIn profile diagnostic, verifies factual claims against collected
evidence, and refuses claims that cannot be supported.

## What It Does

- Accepts a LinkedIn URL for a UAE-based founder, CEO, or fund manager.
- Uses optional search APIs to discover public sources.
- Accepts manual source URLs, which is useful when search APIs are unavailable.
- Fetches and extracts public webpage text.
- Uses LiteLLM so the LLM provider can be swapped with env vars.
- Labels findings as `verified`, `partially_verified`, or `unverified`.
- Produces three public-profile gaps.
- Includes a refused claim and reason.
- Keeps outreach and logged-in data out of scope.

## Quick Start

```
#Python 3.12.14

python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```


```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

Copy .env.example to .env

Edit `.env` and add your provider key plus `LLM_MODEL`.

Run:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For development checks:

```powershell
pip install pytest ruff
pytest
ruff check .
```

Open:

```text
http://127.0.0.1:8000
```

## LiteLLM Provider Examples

```env
LLM_MODEL=groq/openai/gpt-oss-120b
GROQ_API_KEY=...
```

```env
LLM_MODEL=anthropic/claude-3-5-sonnet-20240620
ANTHROPIC_API_KEY=...
```

```env
LLM_MODEL=gemini/gemini-1.5-pro
GEMINI_API_KEY=...
```

## Search

The app can use Brave, Tavily, or SerpAPI when keys are configured. Without a
search key, paste public source URLs manually in the UI.

Primary sources are preferred:

- Official company websites
- Regulator or registry pages
- Founder/company-authored pages
- Fund/company profile pages

## API

`POST /api/diagnostics`

```json
{
  "linkedin_url": "https://www.linkedin.com/in/example/",
  "subject_name": "Example Founder",
  "company_name": "Example Capital",
  "manual_source_urls": ["https://example.com/about"],
  "notes": "UAE-based founder"
}
```

## Hiring Task Submission Checklist

- Five-minute Loom walkthrough.
- Live link, public repo, or workflow export.
- Actual diagnostic output from this app.
- One paragraph on what broke and what you would fix next.
- Honest total hours.

## Limits

LinkedIn is often login-gated. This app does not scrape logged-in LinkedIn data.
It treats the LinkedIn URL as the subject seed and uses public sources for
verification.
