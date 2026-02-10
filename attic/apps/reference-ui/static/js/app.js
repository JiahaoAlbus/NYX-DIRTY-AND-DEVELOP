function setText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = value;
  }
}

async function runEvidence() {
  const seedInput = document.getElementById("seed-input");
  const statusEl = document.getElementById("run-status");
  const rawEl = document.getElementById("evidence-raw");
  const exportLink = document.getElementById("export-link");

  if (!seedInput || !statusEl || !rawEl || !exportLink) {
    return;
  }
  const seedValue = seedInput.value.trim();
  if (!seedValue) {
    statusEl.textContent = "Seed is required.";
    return;
  }
  statusEl.textContent = "Running...";
  rawEl.textContent = "";
  exportLink.setAttribute("href", "#");

  const runResponse = await fetch("/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed: Number(seedValue) })
  });

  const runPayload = await runResponse.json();
  if (!runResponse.ok) {
    statusEl.textContent = runPayload.error || "Run failed.";
    return;
  }
  const runId = runPayload.run_id;
  statusEl.textContent = "Complete";

  const evidenceResponse = await fetch(`/evidence?run_id=${encodeURIComponent(runId)}`);
  const evidenceRaw = await evidenceResponse.text();
  rawEl.textContent = evidenceRaw;

  let parsed;
  try {
    parsed = JSON.parse(evidenceRaw);
  } catch (err) {
    statusEl.textContent = "Evidence parse failed.";
    return;
  }

  setText("state-hash", parsed.state_hash || "");
  setText("receipt-hashes", (parsed.receipt_hashes || []).join(", "));
  setText("replay-ok", String(parsed.replay_ok));

  exportLink.setAttribute("href", `/export.zip?run_id=${encodeURIComponent(runId)}`);
}

window.addEventListener("DOMContentLoaded", () => {
  const runButton = document.getElementById("run-button");
  if (runButton) {
    runButton.addEventListener("click", () => {
      runEvidence().catch(() => {
        const statusEl = document.getElementById("run-status");
        if (statusEl) {
          statusEl.textContent = "Run failed.";
        }
      });
    });
  }
});
