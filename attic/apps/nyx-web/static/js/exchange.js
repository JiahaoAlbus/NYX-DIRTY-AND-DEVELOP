(function () {
  const apiBase = window.NYX_API_BASE || "http://localhost:8090";
  const form = document.getElementById("exchange-form");
  const runButton = document.getElementById("run-btn");
  const stateHash = document.getElementById("state-hash");
  const receiptHashes = document.getElementById("receipt-hashes");
  const replayOk = document.getElementById("replay-ok");
  const exportLink = document.getElementById("export-link");
  const statusText = document.getElementById("status-text");

  function setStatus(text) {
    statusText.textContent = text;
  }

  async function runExchange(payload) {
    const response = await fetch(apiBase + "/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "run failed");
    }
    return data;
  }

  async function loadEvidence(runId) {
    const response = await fetch(apiBase + "/evidence?run_id=" + encodeURIComponent(runId));
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "evidence fetch failed");
    }
    return data;
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    runButton.disabled = true;
    setStatus("Running deterministic exchange flow...");

    const seed = Number(document.getElementById("seed").value);
    const runId = document.getElementById("run-id").value.trim();
    const route = document.getElementById("route").value;

    try {
      await runExchange({
        seed: seed,
        run_id: runId,
        module: "exchange",
        action: "route_swap",
        payload: { route: route },
      });
      const evidence = await loadEvidence(runId);
      stateHash.textContent = evidence.state_hash || "—";
      receiptHashes.textContent = (evidence.receipt_hashes || []).join(", ") || "—";
      replayOk.textContent = String(evidence.replay_ok);
      exportLink.href = apiBase + "/export.zip?run_id=" + encodeURIComponent(runId);
      setStatus("Evidence ready. Testnet Beta. Provided by backend.");
    } catch (err) {
      setStatus("Error: " + err.message);
    } finally {
      runButton.disabled = false;
    }
  });
})();
