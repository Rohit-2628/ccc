document.addEventListener("DOMContentLoaded", () => {
    const deployForm = document.getElementById("deploy-form");
    const overrideForm = document.getElementById("override-form");
    const consoleOutput = document.getElementById("output-console");
    const vaultResult = document.getElementById("vault-result");

    deployForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const manifest = document.getElementById("manifest").value;
        const customCommand = document.getElementById("custom_command").value;

        consoleOutput.textContent = "[*] Submitting container deployment request...";
        try {
            const resp = await fetch("/api/deploy", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ manifest, custom_command: customCommand })
            });
            const data = await resp.json();
            if (data.job && data.job.log) {
                consoleOutput.textContent = data.job.log;
            } else {
                consoleOutput.textContent = JSON.dumps(data, null, 2);
            }
        } catch (err) {
            consoleOutput.textContent = "[ERROR] Network failure: " + err;
        }
    });

    overrideForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const harborMasterId = document.getElementById("harbor_master_id").value;
        const timestamp = document.getElementById("timestamp").value;
        const signature = document.getElementById("signature").value;

        vaultResult.innerHTML = "<p style='color: var(--accent);'>[*] Verifying vault override signature...</p>";
        try {
            const resp = await fetch("/api/production/override", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ harbor_master_id: harborMasterId, timestamp, signature })
            });
            const data = await resp.json();
            if (resp.status === 200 && data.flag) {
                vaultResult.innerHTML = `<div style="background:#064e3b; border:1px solid #059669; padding:15px; border-radius:4px; margin-top:10px;">
                    <h3 style="margin:0; color:#34d399;">OVERRIDE AUTHORIZED</h3>
                    <p style="margin:5px 0 0 0;">Flag: <code>${data.flag}</code></p>
                </div>`;
            } else {
                vaultResult.innerHTML = `<div style="background:#7f1d1d; border:1px solid #dc2626; padding:15px; border-radius:4px; margin-top:10px;">
                    <h3 style="margin:0; color:#f87171;">OVERRIDE DENIED</h3>
                    <p style="margin:5px 0 0 0;">${data.reason || "Verification failed."}</p>
                </div>`;
            }
        } catch (err) {
            vaultResult.innerHTML = `<p style="color: var(--danger);">[ERROR] Network failure: ${err}</p>`;
        }
    });
});
