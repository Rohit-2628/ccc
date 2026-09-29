function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tabId));
    if (activeBtn) activeBtn.classList.add('active');

    const activeTab = document.getElementById(`tab-${tabId}`);
    if (activeTab) activeTab.classList.add('active');

    if (tabId === 'git') loadGitData();
    if (tabId === 'ci') loadCiData();
    if (tabId === 'dind') loadDindData();
    if (tabId === 'registry') loadRegistryData();
    if (tabId === 'production') loadProductionData();
}

async function fetchJson(url, options = {}) {
    try {
        const resp = await fetch(url, options);
        return await resp.json();
    } catch (e) {
        return { error: e.message };
    }
}

// GIT TAB
async function loadGitData() {
    const repos = await fetchJson('/api/git/repos');
    const detailsBox = document.getElementById('git-repo-details');
    if (repos && repos.repositories && repos.repositories.length > 0) {
        const r = repos.repositories[0];
        detailsBox.innerHTML = `
            <div><strong>Repository:</strong> ${r.full_name}</div>
            <div><strong>Default Branch:</strong> ${r.default_branch}</div>
            <div><strong>Description:</strong> ${r.description}</div>
        `;
    }

    const commits = await fetchJson('/api/git/repos/defense-network/commits');
    const commitsBox = document.getElementById('git-commits-list');
    if (commits && commits.commits) {
        commitsBox.innerHTML = commits.commits.map(c => `
            <div style="padding: 6px 0; border-bottom: 1px solid var(--border-color);">
                <code>${c.hash.substring(0, 7)}</code> &bull; <strong>${c.message}</strong><br>
                <span style="font-size:11px; color:var(--text-muted);">${c.author} &bull; ${c.date}</span>
            </div>
        `).join('');
    }

    const tree = await fetchJson('/api/git/repos/defense-network/tree');
    const treeBox = document.getElementById('git-files-tree');
    if (tree && tree.files) {
        treeBox.innerHTML = tree.files.map(f => `
            <div style="padding: 4px 0;">
                📄 <a href="javascript:void(0)" onclick="viewGitFile('${f}')" style="color:var(--accent-cyan); text-decoration:none;">${f}</a>
            </div>
        `).join('');
    }
}

async function viewGitFile(filepath) {
    const res = await fetchJson(`/api/git/repos/defense-network/blob/${encodeURIComponent(filepath)}`);
    const viewer = document.getElementById('git-file-viewer');
    const code = document.getElementById('viewer-code');
    const name = document.getElementById('viewer-filename');
    if (res && res.content !== undefined) {
        name.innerText = filepath;
        code.innerText = res.content;
        viewer.style.display = 'block';
    }
}

function closeViewer() {
    document.getElementById('git-file-viewer').style.display = 'none';
}

// CI TAB
async function loadCiData() {
    const status = await fetchJson('/api/ci/status');
    const statusBox = document.getElementById('ci-runner-status');
    if (status && status.active_runners) {
        const r = status.active_runners[0];
        statusBox.innerHTML = `
            <div><strong>Service:</strong> ${status.service} v${status.version}</div>
            <div><strong>Active Runner:</strong> <code>${r.runner_id}</code></div>
            <div><strong>Runner Status:</strong> <span class="status-badge status-success">${r.status}</span></div>
            <div><strong>Inner Daemon:</strong> <code>${r.dind_endpoint}</code> (${r.docker_version})</div>
        `;
    }

    const builds = await fetchJson('/api/ci/builds');
    const buildsBox = document.getElementById('ci-builds-list');
    if (builds && builds.builds) {
        buildsBox.innerHTML = builds.builds.map(b => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding: 6px 0; border-bottom: 1px solid var(--border-color);">
                <div>
                    <strong>Job #${b.build_id}</strong> &bull; ${b.repo}:${b.branch} &bull; 
                    <span class="status-badge ${b.status === 'SUCCESS' ? 'status-success' : 'status-failed'}">${b.status}</span>
                </div>
                <div>
                    <button class="btn-sm" onclick="viewCiLog('${b.build_id}')">View Log</button>
                </div>
            </div>
        `).join('');
    }
}

async function viewCiLog(buildId) {
    const build = await fetchJson(`/api/ci/builds/${buildId}`);
    const viewer = document.getElementById('ci-log-viewer');
    const title = document.getElementById('ci-log-title');
    const content = document.getElementById('ci-log-content');
    if (build && build.log) {
        title.innerText = `Build #${build.build_id} Console Log (${build.status})`;
        content.innerText = build.log;
        viewer.style.display = 'block';
    }
}

function closeLogViewer() {
    document.getElementById('ci-log-viewer').style.display = 'none';
}

async function triggerBuild(e) {
    e.preventDefault();
    const repo = document.getElementById('ci-repo').value;
    const branch = document.getElementById('ci-branch').value;
    const custom_command = document.getElementById('ci-custom-cmd').value;

    const res = await fetchJson('/api/ci/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo, branch, custom_command })
    });

    if (res && res.build) {
        loadCiData();
        viewCiLog(res.build.build_id);
    }
}

// DIND TAB
async function loadDindData() {
    const list = document.getElementById('dind-images-list');
    // Query catalog and manifest info
    const res = await fetchJson('/registry/v2/_catalog');
    if (res && res.repositories) {
        list.innerHTML = `
            <div class="code-box">
                <strong>Discovered Images in Inner Environment:</strong><br>
                - <code>latveria/ci-builder-base:latest</code> (Worker Runtime)<br>
                - <code>registry.latveria.local:5000/defense/sentinel-node:v2.1.0</code> (Built Application)<br>
                - <code>registry.latveria.local:5000/internal/deployment-signer:v1.0.0</code> (Deployment Signer Module)
            </div>
        `;
    }
}

// REGISTRY TAB
async function loadRegistryData() {
    const catalog = await fetchJson('/registry/v2/_catalog');
    const catBox = document.getElementById('registry-catalog-list');
    if (catalog && catalog.repositories) {
        catBox.innerHTML = catalog.repositories.map(r => `
            <div style="padding: 6px 0; border-bottom: 1px solid var(--border-color);">
                📦 <strong>${r}</strong>
                <button class="btn-sm" style="margin-left: 10px;" onclick="viewManifest('${r}', 'latest')">View Manifest</button>
            </div>
        `).join('');
    }
}

async function viewManifest(repo, tag) {
    const mf = await fetchJson(`/registry/v2/${repo}/manifests/${tag}`);
    const viewer = document.getElementById('registry-manifest-viewer');
    const title = document.getElementById('registry-manifest-title');
    const content = document.getElementById('registry-manifest-content');
    title.innerText = `Manifest: ${repo}:${tag}`;
    content.innerText = JSON.stringify(mf, null, 2);
    viewer.style.display = 'block';
}

function closeManifestViewer() {
    document.getElementById('registry-manifest-viewer').style.display = 'none';
}

// PRODUCTION TAB
async function loadProductionData() {
    const status = await fetchJson('/api/production/status');
    const box = document.getElementById('prod-status-box');
    if (status) {
        box.innerHTML = `
            <div><strong>Cluster:</strong> ${status.cluster_name}</div>
            <div><strong>Status:</strong> <span class="status-badge ${status.unlocked ? 'status-success' : 'status-failed'}">${status.status}</span></div>
            <div><strong>Defense Shield:</strong> ${status.defense_shield}</div>
            <div><strong>Active Image:</strong> <code>${status.active_image}</code></div>
            <div><strong>Required Signer:</strong> <code>${status.deployment_policy.allowed_signer}</code></div>
        `;
    }
}

async function submitDeployment(e) {
    e.preventDefault();
    const image = document.getElementById('deploy-image').value;
    const signer_id = document.getElementById('deploy-signer-id').value;
    const signing_key = document.getElementById('deploy-signing-key').value;
    const action = document.getElementById('deploy-action').value;

    const res = await fetchJson('/api/production/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image, signer_id, signing_key, action })
    });

    const resBox = document.getElementById('deploy-result-box');
    if (res && res.flag) {
        resBox.innerHTML = `
            <div class="code-box" style="border-color:var(--accent-green); background-color: rgba(16, 185, 129, 0.1);">
                <strong style="color:var(--accent-green);">🎉 DEPLOYMENT GRANTED &amp; CORE UNLOCKED!</strong><br>
                <div><strong>Message:</strong> ${res.message}</div>
                <div style="margin-top:8px; font-size:14px;"><strong>FLAG:</strong> <code>${res.flag}</code></div>
            </div>
        `;
        loadProductionData();
    } else {
        resBox.innerHTML = `
            <div class="code-box" style="border-color:var(--accent-red); background-color: rgba(239, 68, 68, 0.1);">
                <strong style="color:var(--accent-red);">❌ DEPLOYMENT REJECTED:</strong> ${res.error || 'Validation failed.'}
            </div>
        `;
    }
}

// TERMINAL / API
async function runApiGet(url) {
    document.getElementById('api-url').value = url;
    await executeApiQuery();
}

async function executeApiQuery() {
    const url = document.getElementById('api-url').value;
    const respBox = document.getElementById('api-response-box');
    respBox.innerText = 'Sending request...';
    try {
        const resp = await fetch(url);
        const text = await resp.text();
        try {
            const formatted = JSON.stringify(JSON.parse(text), null, 2);
            respBox.innerText = `HTTP ${resp.status}\n\n${formatted}`;
        } catch {
            respBox.innerText = `HTTP ${resp.status}\n\n${text}`;
        }
    } catch (e) {
        respBox.innerText = `Error: ${e.message}`;
    }
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    loadGitData();
});
