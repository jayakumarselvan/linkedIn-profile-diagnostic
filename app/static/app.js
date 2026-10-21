const form = document.querySelector("#diagnostic-form");
const output = document.querySelector("#output");
const loading = document.querySelector("#loading");
const emptyState = document.querySelector("#empty-state");

function lines(value) {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function sourceLinks(urls) {
  if (!urls?.length) return "";
  return `<ol class="sources">${urls
    .map((url) => `<li><a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(url)}</a></li>`)
    .join("")}</ol>`;
}

function renderDiagnostic(data) {
  const diagnostic = data.diagnostic;
  output.innerHTML = `
    <header>
      <p class="eyebrow">One-page diagnostic</p>
      <h2>${escapeHtml(diagnostic.subject_name)}${diagnostic.company_name ? `, ${escapeHtml(diagnostic.company_name)}` : ""}</h2>
      <p class="summary">${escapeHtml(diagnostic.executive_summary)}</p>
    </header>

    <section class="section">
      <h3>Verified Findings</h3>
      <ul class="list">
        ${diagnostic.findings
          .map(
            (finding) => `
          <li class="item">
            <div class="meta"><span class="badge ${escapeHtml(finding.status)}">${escapeHtml(finding.status)}</span></div>
            <p>${escapeHtml(finding.text)}</p>
            <p>${escapeHtml(finding.explanation)}</p>
            ${sourceLinks(finding.supporting_sources)}
          </li>`
          )
          .join("")}
      </ul>
    </section>

    <section class="section">
      <h3>Three Biggest Public Profile Gaps</h3>
      <ul class="list">
        ${diagnostic.profile_gaps
          .map(
            (gap) => `
          <li class="item">
            <div class="meta"><span class="badge ${escapeHtml(gap.severity)}">${escapeHtml(gap.severity)}</span></div>
            <p><strong>${escapeHtml(gap.title)}</strong></p>
            <p>${escapeHtml(gap.evidence)}</p>
            <p>${escapeHtml(gap.recommendation)}</p>
          </li>`
          )
          .join("")}
      </ul>
    </section>

    <section class="section">
      <h3>Refused Claim</h3>
      <div class="item">
        <p><strong>${escapeHtml(diagnostic.refused_claim.claim)}</strong></p>
        <p>${escapeHtml(diagnostic.refused_claim.reason)}</p>
        ${sourceLinks(diagnostic.refused_claim.attempted_sources)}
      </div>
    </section>

    <section class="section">
      <h3>Sources</h3>
      ${sourceLinks(diagnostic.source_urls)}
    </section>

    <section class="section">
      <h3>Next Steps</h3>
      <ul>
        ${diagnostic.next_steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}
      </ul>
    </section>
  `;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submit = form.querySelector("button");
  const formData = new FormData(form);
  const payload = {
    linkedin_url: formData.get("linkedin_url"),
    subject_name: formData.get("subject_name"),
    company_name: formData.get("company_name") || null,
    manual_source_urls: lines(formData.get("manual_source_urls") || ""),
    notes: formData.get("notes") || null,
  };

  submit.disabled = true;
  emptyState.classList.add("hidden");
  output.classList.add("hidden");
  loading.classList.remove("hidden");

  try {
    const response = await fetch("/api/diagnostics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail?.message || data.detail || "Diagnostic failed");
    }
    renderDiagnostic(data);
    output.classList.remove("hidden");
  } catch (error) {
    output.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
    output.classList.remove("hidden");
  } finally {
    submit.disabled = false;
    loading.classList.add("hidden");
  }
});
