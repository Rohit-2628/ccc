document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    const flowSteps = document.querySelectorAll('.flow-step');
    const tabContents = document.querySelectorAll('.tab-content');

    flowSteps.forEach(step => {
        step.addEventListener('click', () => {
            const targetTab = step.getAttribute('data-tab');
            flowSteps.forEach(s => s.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));

            step.classList.add('active');
            const content = document.getElementById(`tab-${targetTab}`);
            if (content) content.classList.add('active');

            if (targetTab === 'packages') loadPackages();
            if (targetTab === 'ci') loadBuilds();
            if (targetTab === 'registry') loadRegistry();
            if (targetTab === 'deployment') loadDeployment();
        });
    });

    // Reset button
    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            if (!confirm('Restore environment to clean seed snapshot?')) return;
            try {
                const res = await fetch('/api/reset', { method: 'POST' });
                const data = await res.json();
                alert(data.message || 'Environment reset successful!');
                location.reload();
            } catch (err) {
                alert('Reset failed: ' + err);
            }
        });
    }

    // --- Package Repository Tab ---
    const packagesList = document.getElementById('packages-list');
    const pkgSearchInput = document.getElementById('pkg-search');
    const refreshPkgsBtn = document.getElementById('refresh-pkgs-btn');
    const pkgModal = document.getElementById('package-detail-modal');
    const modalPkgName = document.getElementById('modal-pkg-name');
    const modalPkgBody = document.getElementById('modal-pkg-body');
    const closeDrawer = document.getElementById('close-drawer');

    if (closeDrawer) {
        closeDrawer.addEventListener('click', () => {
            pkgModal.classList.add('hidden');
        });
    }

    if (refreshPkgsBtn) {
        refreshPkgsBtn.addEventListener('click', () => loadPackages());
    }

    if (pkgSearchInput) {
        pkgSearchInput.addEventListener('input', (e) => {
            const q = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.pkg-card');
            cards.forEach(card => {
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(q) ? 'block' : 'none';
            });
        });
    }

    async function loadPackages() {
        if (!packagesList) return;
        packagesList.innerHTML = '<div class="loading">Loading package metadata from repository...</div>';
        try {
            const res = await fetch('/api/packages');
            const data = await res.json();
            const pkgs = data.packages || [];
            
            if (pkgs.length === 0) {
                packagesList.innerHTML = '<div>No packages published in internal registry.</div>';
                return;
            }

            packagesList.innerHTML = '';
            pkgs.forEach(pkg => {
                const card = document.createElement('div');
                card.className = 'pkg-card';
                card.innerHTML = `
                    <div class="pkg-card-title">${escapeHtml(pkg.name)}</div>
                    <div class="pkg-card-desc">${escapeHtml(pkg.description || 'No description')}</div>
                    <div class="pkg-card-meta">
                        <span>Latest: <strong>${escapeHtml(pkg.latest || 'n/a')}</strong></span>
                        <span>Versions: ${pkg.versions ? pkg.versions.length : 0}</span>
                    </div>
                `;
                card.addEventListener('click', () => inspectPackage(pkg.name));
                packagesList.appendChild(card);
            });
        } catch (err) {
            packagesList.innerHTML = `<div class="error">Failed to load packages: ${err}</div>`;
        }
    }

    async function inspectPackage(pkgName) {
        if (!pkgModal || !modalPkgBody) return;
        modalPkgName.textContent = `Package: ${pkgName}`;
        modalPkgBody.innerHTML = '<div class="loading">Fetching package version history and metadata...</div>';
        pkgModal.classList.remove('hidden');

        try {
            const res = await fetch(`/api/packages/${encodeURIComponent(pkgName)}`);
            const meta = await res.json();
            
            let versionsHtml = '';
            const versions = meta.versions || {};
            for (const [vKey, vData] of Object.entries(versions)) {
                const dist = vData.dist || {};
                const prov = vData.provenance || {};
                versionsHtml += `
                    <div class="code-box" style="margin-bottom: 1rem;">
                        <div class="code-header">VERSION: ${escapeHtml(vKey)} ${vKey === meta['dist-tags']?.latest ? '<span class="badge badge-green">LATEST</span>' : ''}</div>
                        <div style="padding: 0.8rem; font-family: var(--font-mono); font-size: 0.8rem;">
                            <div><strong>SHA256:</strong> ${escapeHtml(dist.shasum || 'n/a')}</div>
                            <div><strong>Author:</strong> ${escapeHtml(prov.author || 'unknown')} (Commit: ${escapeHtml(prov.commit || 'n/a')})</div>
                            ${prov.note ? `<div style="color: var(--accent-gold);"><strong>Note:</strong> ${escapeHtml(prov.note)}</div>` : ''}
                            <div style="margin-top: 0.5rem;">
                                <a href="${dist.tarball}" class="btn-primary" style="display: inline-block; text-decoration: none; padding: 0.2rem 0.6rem; font-size: 0.75rem;" download>DOWNLOAD TARBALL (.tgz)</a>
                            </div>
                        </div>
                    </div>
                `;
            }

            modalPkgBody.innerHTML = `
                <div style="margin-bottom: 1rem; color: var(--text-muted); font-size: 0.85rem;">
                    ${escapeHtml(meta.description || '')}
                </div>
                <h4>AVAILABLE VERSIONS & ARTIFACTS</h4>
                ${versionsHtml}
                <div style="margin-top: 1rem;">
                    <h4>RAW METADATA JSON</h4>
                    <pre><code>${escapeHtml(JSON.stringify(meta, null, 2))}</code></pre>
                </div>
            `;
        } catch (err) {
            modalPkgBody.innerHTML = `<div class="error">Failed to inspect package: ${err}</div>`;
        }
    }

    // --- CI/CD Pipeline Tab ---
    const buildsTbody = document.getElementById('builds-tbody');
    const buildLogConsole = document.getElementById('build-log-console');
    const activeBuildBadge = document.getElementById('active-build-badge');
    const triggerBuildBtn = document.getElementById('trigger-build-btn');

    if (triggerBuildBtn) {
        triggerBuildBtn.addEventListener('click', async () => {
            triggerBuildBtn.disabled = true;
            triggerBuildBtn.textContent = 'BUILDING...';
            try {
                const res = await fetch('/api/ci/build', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pipeline: 'doombot-production-build', branch: 'main' })
                });
                const build = await res.json();
                await loadBuilds();
                displayBuildLog(build);
            } catch (err) {
                alert('Build trigger failed: ' + err);
            } finally {
                triggerBuildBtn.disabled = false;
                triggerBuildBtn.textContent = 'TRIGGER NEW BUILD';
            }
        });
    }

    async function loadBuilds() {
        if (!buildsTbody) return;
        try {
            const res = await fetch('/api/ci/builds');
            const data = await res.json();
            const builds = data.builds || [];
            
            buildsTbody.innerHTML = '';
            builds.forEach(b => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>#${escapeHtml(b.build_id)}</strong></td>
                    <td>${escapeHtml(b.pipeline)}</td>
                    <td><span class="badge badge-green">${escapeHtml(b.status)}</span></td>
                    <td style="font-size: 0.75rem;">${escapeHtml(b.output_image || 'n/a')}</td>
                    <td><button class="btn-ghost" style="padding: 0.2rem 0.4rem;">LOG</button></td>
                `;
                tr.addEventListener('click', () => fetchBuildDetail(b.build_id));
                buildsTbody.appendChild(tr);
            });

            if (builds.length > 0) {
                fetchBuildDetail(builds[builds.length - 1].build_id);
            }
        } catch (err) {
            buildsTbody.innerHTML = `<tr><td colspan="5" class="error">Failed to load builds: ${err}</td></tr>`;
        }
    }

    async function fetchBuildDetail(buildId) {
        try {
            const res = await fetch(`/api/ci/builds/${buildId}`);
            const detail = await res.json();
            displayBuildLog(detail);
        } catch (err) {
            buildLogConsole.textContent = `Failed to fetch build details: ${err}`;
        }
    }

    function displayBuildLog(build) {
        if (!buildLogConsole) return;
        activeBuildBadge.textContent = `BUILD #${build.build_id}`;
        buildLogConsole.textContent = build.log || JSON.stringify(build, null, 2);
    }

    // --- Image Registry Tab ---
    const registryContent = document.getElementById('registry-content');
    const refreshRegistryBtn = document.getElementById('refresh-registry-btn');

    if (refreshRegistryBtn) {
        refreshRegistryBtn.addEventListener('click', () => loadRegistry());
    }

    async function loadRegistry() {
        if (!registryContent) return;
        registryContent.innerHTML = '<div class="loading">Querying OCI v2 catalog...</div>';
        try {
            const res = await fetch('/registry/v2/_catalog');
            const data = await res.json();
            const repos = data.repositories || [];
            
            let html = '';
            for (const repo of repos) {
                const tagRes = await fetch(`/registry/v2/${repo}/tags/list`);
                const tagData = await tagRes.json();
                const tags = tagData.tags || [];
                
                html += `
                    <div class="card" style="margin-bottom: 1rem;">
                        <div class="card-header">
                            <h3>Repository: <span style="color: var(--accent-cyan); font-family: var(--font-mono);">${escapeHtml(repo)}</span></h3>
                            <span class="badge badge-blue">OCI v2</span>
                        </div>
                        <div class="card-body">
                            <p style="font-family: var(--font-mono); font-size: 0.85rem; margin-bottom: 0.5rem;">Tags: ${tags.map(t => `<span class="badge badge-green" style="margin-right: 0.4rem;">${escapeHtml(t)}</span>`).join('')}</p>
                            <div style="margin-top: 1rem;">
                                <button class="btn-ghost" onclick="inspectManifest('${escapeHtml(repo)}', '${escapeHtml(tags[0] || 'latest')}')">INSPECT MANIFEST (${escapeHtml(tags[0] || 'latest')})</button>
                            </div>
                            <div id="manifest-box-${repo.replace('/', '-')}" class="code-box" style="display: none; margin-top: 1rem;"></div>
                        </div>
                    </div>
                `;
            }
            registryContent.innerHTML = html || '<div>No repositories found in registry.</div>';
        } catch (err) {
            registryContent.innerHTML = `<div class="error">Failed to query registry: ${err}</div>`;
        }
    }

    window.inspectManifest = async function(repo, tag) {
        const box = document.getElementById(`manifest-box-${repo.replace('/', '-')}`);
        if (!box) return;
        box.style.display = 'block';
        box.innerHTML = '<div class="loading">Fetching manifest...</div>';
        try {
            const res = await fetch(`/registry/v2/${repo}/manifests/${tag}`);
            const data = await res.json();
            box.innerHTML = `
                <div class="code-header">MANIFEST: ${escapeHtml(repo)}:${escapeHtml(tag)}</div>
                <pre><code>${escapeHtml(JSON.stringify(data, null, 2))}</code></pre>
            `;
        } catch (err) {
            box.innerHTML = `<div class="error">Failed to fetch manifest: ${err}</div>`;
        }
    };

    // --- Production Deployment Tab ---
    const deploymentStatusBox = document.getElementById('deployment-status-box');
    const overrideForm = document.getElementById('override-form');
    const overrideResult = document.getElementById('override-result');

    async function loadDeployment() {
        if (!deploymentStatusBox) return;
        deploymentStatusBox.innerHTML = '<div class="loading">Querying production runtime...</div>';
        try {
            const res = await fetch('/api/deployment/status');
            const data = await res.json();
            
            deploymentStatusBox.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
                    <div style="background: #04070a; padding: 1rem; border: 1px solid var(--border-color); border-radius: 4px;">
                        <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">MAINFRAME CLUSTER</div>
                        <div style="font-size: 1rem; font-weight: 700; color: var(--accent-cyan); font-family: var(--font-mono);">${escapeHtml(data.cluster || 'n/a')}</div>
                    </div>
                    <div style="background: #04070a; padding: 1rem; border: 1px solid var(--border-color); border-radius: 4px;">
                        <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">ACTIVE DEPLOYED IMAGE</div>
                        <div style="font-size: 0.85rem; font-weight: 600; color: var(--accent-emerald); font-family: var(--font-mono);">${escapeHtml(data.active_image || 'n/a')}</div>
                    </div>
                </div>
                <div class="code-box">
                    <div class="code-header">ACTIVE RUNTIME SUBMODULES</div>
                    <pre><code>${escapeHtml(JSON.stringify(data.active_modules, null, 2))}</code></pre>
                </div>
            `;
        } catch (err) {
            deploymentStatusBox.innerHTML = `<div class="error">Failed to query production status: ${err}</div>`;
        }
    }

    if (overrideForm) {
        overrideForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const headerVal = document.getElementById('override-header').value.trim();
            const payloadStr = document.getElementById('override-payload').value.trim();
            
            overrideResult.className = 'result-box';
            overrideResult.classList.remove('hidden');
            overrideResult.textContent = 'Transmitting maintainer override...';

            let payloadJson;
            try {
                payloadJson = JSON.parse(payloadStr);
            } catch (err) {
                overrideResult.className = 'result-box error';
                overrideResult.textContent = 'Invalid JSON payload format: ' + err.message;
                return;
            }

            try {
                const res = await fetch('/api/deployment/override', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Latveria-Override-Key': headerVal
                    },
                    body: JSON.stringify(payloadJson)
                });
                const result = await res.json();

                if (res.ok && result.status === 'OVERRIDE_GRANTED') {
                    overrideResult.className = 'result-box success';
                    overrideResult.innerHTML = `
                        <div style="font-weight: 800; font-size: 1.1rem; margin-bottom: 0.5rem;">✓ ${escapeHtml(result.message)}</div>
                        <div><strong>AUTHORIZATION:</strong> ${escapeHtml(result.authorization)}</div>
                        <div style="margin-top: 0.8rem; background: #000; padding: 0.8rem; border: 1px dashed var(--primary-green); font-size: 1.1rem; color: #fff;">
                            <strong>FLAG:</strong> <span style="color: #4ade80;">${escapeHtml(result.flag)}</span>
                        </div>
                    `;
                } else {
                    overrideResult.className = 'result-box error';
                    overrideResult.innerHTML = `
                        <div style="font-weight: 700;">✗ ${escapeHtml(result.error || 'ACCESS_DENIED')}</div>
                        <div>${escapeHtml(result.message || 'Override request rejected')}</div>
                    `;
                }
            } catch (err) {
                overrideResult.className = 'result-box error';
                overrideResult.textContent = 'Network communication error: ' + err.message;
            }
        });
    }

    function escapeHtml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
