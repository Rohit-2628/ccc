#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Public Gateway & Ingress Orchestrator
Port: 0.0.0.0:80
Routes external player traffic to internal challenge-local microservices.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from flask import Flask, request, jsonify, render_template_string, Response

# Add challenge root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.mesh_crypto import ensure_pki_initialized, reset_mesh_state

app = Flask(__name__)
ensure_pki_initialized()

INTERNAL_ROUTES = {
    "service_a": "http://127.0.0.1:8081",
    "service_b": "http://127.0.0.1:8082",
    "admin": "http://127.0.0.1:8083"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Latverian Sovereign Citadel — Microservice Mesh Control Plane</title>
    <style>
        :root {
            --bg-primary: #0b0f19;
            --bg-secondary: #121826;
            --bg-tertiary: #1b2438;
            --accent-green: #10b981;
            --accent-emerald: #059669;
            --accent-red: #ef4444;
            --accent-amber: #f59e0b;
            --accent-cyan: #06b6d4;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --border-color: #2e384d;
            --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            padding: 24px;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-badge {
            background: var(--accent-emerald);
            color: #fff;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        h1 {
            font-size: 20px;
            letter-spacing: 0.5px;
        }

        .status-pill {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 13px;
            font-family: var(--font-mono);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-green);
            box-shadow: 0 0 8px var(--accent-green);
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        @media (max-width: 900px) {
            .grid { grid-template-columns: 1fr; }
        }

        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--accent-cyan);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .topology-node {
            background: var(--bg-tertiary);
            border-left: 4px solid var(--accent-cyan);
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .topology-node.low-trust {
            border-left-color: var(--accent-amber);
        }

        .topology-node.high-trust {
            border-left-color: var(--accent-green);
        }

        .topology-node.admin-vault {
            border-left-color: var(--accent-red);
        }

        .node-info h4 {
            font-size: 14px;
            margin-bottom: 2px;
        }

        .node-info p {
            font-size: 12px;
            color: var(--text-muted);
            font-family: var(--font-mono);
        }

        .badge {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }

        .badge-low { background: rgba(245, 158, 11, 0.2); color: var(--accent-amber); }
        .badge-high { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }
        .badge-admin { background: rgba(239, 68, 68, 0.2); color: var(--accent-red); }

        pre, code {
            font-family: var(--font-mono);
            font-size: 12px;
        }

        .code-block {
            background: #060911;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 12px;
            max-height: 260px;
            overflow-y: auto;
            color: #d1d5db;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .btn {
            background: var(--accent-emerald);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: opacity 0.2s;
        }

        .btn:hover {
            opacity: 0.9;
        }

        .btn-outline {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-main);
        }

        .form-group {
            margin-bottom: 12px;
        }

        label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
            text-transform: uppercase;
        }

        input, select, textarea {
            width: 100%;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 8px 12px;
            border-radius: 4px;
            font-family: var(--font-mono);
            font-size: 13px;
        }

        input:focus, textarea:focus, select:focus {
            outline: 1px solid var(--accent-cyan);
            border-color: var(--accent-cyan);
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <span class="brand-badge">CITADEL GRID</span>
            <h1>Sovereign Microservice Mesh Control Gateway</h1>
        </div>
        <div class="status-pill">
            <div class="status-dot"></div>
            <span>MESH INGRESS ACTIVE [TCP/80]</span>
        </div>
    </header>

    <div class="grid">
        <!-- Topology View -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Mesh Architecture & Service Dependencies</span>
            </div>
            
            <div class="topology-node">
                <div class="node-info">
                    <h4>Public Gateway Ingress</h4>
                    <p>Interface: TCP/80 (External Entry)</p>
                </div>
                <span class="badge" style="background: #2563eb; color: #fff;">INGRESS</span>
            </div>

            <div style="text-align: center; color: var(--text-muted); margin: -4px 0 8px 0;">▼ routes public API</div>

            <div class="topology-node low-trust">
                <div class="node-info">
                    <h4>Service A — Edge Telemetry Agent</h4>
                    <p>Internal: 127.0.0.1:8081 | spiffe://latveria.citadel/sa/telemetry-agent</p>
                </div>
                <span class="badge badge-low">LOW TRUST</span>
            </div>

            <div style="text-align: center; color: var(--text-muted); margin: -4px 0 8px 0;">▼ Citadel mTLS Identity Assertion</div>

            <div class="topology-node high-trust">
                <div class="node-info">
                    <h4>Service B — Core Controller</h4>
                    <p>Internal: 127.0.0.1:8082 | Enforces Root CA Identity Verification</p>
                </div>
                <span class="badge badge-high">HIGH PRIVILEGE</span>
            </div>

            <div style="text-align: center; color: var(--text-muted); margin: -4px 0 8px 0;">▼ Admin Grant Ticket (LATV-ADMIN-TICKET-*)</div>

            <div class="topology-node admin-vault">
                <div class="node-info">
                    <h4>Admin Service — Citadel Sovereign Vault</h4>
                    <p>Internal: 127.0.0.1:8083 | Protected Master Flag Custodian</p>
                </div>
                <span class="badge badge-admin">SOVEREIGN ROOT</span>
            </div>
        </div>

        <!-- Interactive API Studio -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Mesh Request Dispatcher</span>
            </div>

            <div class="form-group">
                <label>HTTP Method & Target Endpoint</label>
                <div style="display: flex; gap: 8px;">
                    <select id="reqMethod" style="width: 100px;">
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                    </select>
                    <input type="text" id="reqPath" value="/api/v1/telemetry/status" placeholder="/api/v1/...">
                </div>
            </div>

            <div class="form-group">
                <label>Mesh Identity Header (X-Citadel-Identity-Cert / Authorization)</label>
                <textarea id="reqHeaders" rows="3" placeholder="X-Citadel-Identity-Cert: -----BEGIN CERTIFICATE-----..."></textarea>
            </div>

            <div class="form-group">
                <label>JSON Request Body (Optional)</label>
                <input type="text" id="reqBody" placeholder='{"action": "grant-admin-ticket"}'>
            </div>

            <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                <button class="btn" onclick="sendMeshRequest()">Dispatch Request</button>
                <button class="btn btn-outline" onclick="loadSample('telemetry')">Sample: Telemetry</button>
                <button class="btn btn-outline" onclick="loadSample('diagnostics')">Sample: Diagnostics</button>
                <button class="btn btn-outline" onclick="loadSample('core')">Sample: Core Status</button>
            </div>

            <label>Response Console</label>
            <div id="responseConsole" class="code-block">Waiting for request dispatch...</div>
        </div>
    </div>

    <div style="margin-top: 24px;" class="card">
        <div class="card-header">
            <span class="card-title">Mesh Endpoint Reference</span>
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; font-family: var(--font-mono);">
            <thead>
                <tr style="text-align: left; border-bottom: 1px solid var(--border-color); color: var(--accent-cyan);">
                    <th style="padding: 8px;">Path</th>
                    <th style="padding: 8px;">Target Service</th>
                    <th style="padding: 8px;">Identity / Auth Requirement</th>
                    <th style="padding: 8px;">Description</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px; color: var(--accent-green);">GET /api/v1/telemetry/status</td>
                    <td style="padding: 8px;">Service A (Telemetry)</td>
                    <td style="padding: 8px;">None (Public via Gateway)</td>
                    <td style="padding: 8px;">Mesh telemetry metrics & health</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px; color: var(--accent-green);">GET /api/v1/telemetry/config</td>
                    <td style="padding: 8px;">Service A (Telemetry)</td>
                    <td style="padding: 8px;">None (Public via Gateway)</td>
                    <td style="padding: 8px;">Mesh topology and policy specifications</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px; color: var(--accent-green);">GET /api/v1/diagnostics/export</td>
                    <td style="padding: 8px;">Service A (Telemetry)</td>
                    <td style="padding: 8px;">None (Public via Gateway)</td>
                    <td style="padding: 8px;">Diagnostic bundle with Service A mesh credentials</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px; color: var(--accent-amber);">POST /api/v1/core/grant-admin-ticket</td>
                    <td style="padding: 8px;">Service B (Core Controller)</td>
                    <td style="padding: 8px;">X-Citadel-Identity-Cert (Orchestrator)</td>
                    <td style="padding: 8px;">Issues Admin Ticket for privileged identity</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: var(--accent-red);">POST /api/v1/admin/unlock-vault</td>
                    <td style="padding: 8px;">Admin Service (Vault)</td>
                    <td style="padding: 8px;">Authorization: Bearer &lt;TICKET&gt;</td>
                    <td style="padding: 8px;">Unlocks Sovereign Vault and outputs flag</td>
                </tr>
            </tbody>
        </table>
    </div>

    <script>
        function loadSample(type) {
            const method = document.getElementById('reqMethod');
            const path = document.getElementById('reqPath');
            const headers = document.getElementById('reqHeaders');
            const body = document.getElementById('reqBody');

            if (type === 'telemetry') {
                method.value = 'GET';
                path.value = '/api/v1/telemetry/status';
                headers.value = '';
                body.value = '';
            } else if (type === 'diagnostics') {
                method.value = 'GET';
                path.value = '/api/v1/diagnostics/export';
                headers.value = '';
                body.value = '';
            } else if (type === 'core') {
                method.value = 'POST';
                path.value = '/api/v1/core/grant-admin-ticket';
                headers.value = 'X-Citadel-Identity-Cert: <INSERT_CLIENT_CERT_CHAIN_HERE>';
                body.value = '{}';
            }
        }

        async function sendMeshRequest() {
            const method = document.getElementById('reqMethod').value;
            const path = document.getElementById('reqPath').value;
            const headersRaw = document.getElementById('reqHeaders').value;
            const bodyRaw = document.getElementById('reqBody').value;
            const consoleEl = document.getElementById('responseConsole');

            consoleEl.innerText = 'Dispatching request to ' + path + '...';

            const reqHeaders = {};
            if (headersRaw.trim()) {
                headersRaw.split('\\n').forEach(line => {
                    const idx = line.indexOf(':');
                    if (idx > 0) {
                        reqHeaders[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
                    }
                });
            }

            try {
                const options = {
                    method: method,
                    headers: reqHeaders
                };

                if (method === 'POST' && bodyRaw.trim()) {
                    options.headers['Content-Type'] = 'application/json';
                    options.body = bodyRaw;
                }

                const res = await fetch(path, options);
                const text = await res.text();
                let formatted = text;
                try {
                    const obj = JSON.parse(text);
                    formatted = JSON.stringify(obj, null, 2);
                } catch(e) {}

                consoleEl.innerText = `[HTTP ${res.status} ${res.statusText}]\\n\\n` + formatted;
            } catch (err) {
                consoleEl.innerText = `[Dispatch Error]\\n` + err.message;
            }
        }
    </script>
</body>
</html>
"""


def forward_to_internal(target_base_url: str, path_suffix: str):
    """Generic forwarder that proxies request to internal loopback service preserving headers."""
    target_url = f"{target_base_url}{path_suffix}"
    if request.query_string:
        target_url += f"?{request.query_string.decode('utf-8')}"

    req_headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ["host", "content-length"]:
            req_headers[key] = value

    data = request.get_data() if request.method in ["POST", "PUT", "PATCH"] else None

    req = urllib.request.Request(
        target_url,
        data=data,
        headers=req_headers,
        method=request.method
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            resp_body = response.read()
            resp_status = response.status
            resp_headers = dict(response.getheaders())
            return Response(resp_body, status=resp_status, headers=resp_headers)
    except urllib.error.HTTPError as e:
        resp_body = e.read()
        resp_status = e.code
        resp_headers = dict(e.headers)
        return Response(resp_body, status=resp_status, headers=resp_headers)
    except Exception as e:
        return jsonify({
            "status": "GATEWAY_ERROR",
            "error": "UpstreamUnavailable",
            "message": f"Failed to contact internal microservice at {target_url}: {str(e)}"
        }), 502


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/v1/topology", methods=["GET"])
def topology():
    return jsonify({
        "mesh_name": "Latveria Citadel Microservice Mesh",
        "gateway_interface": "TCP/80",
        "services": {
            "gateway": {"role": "Public Ingress", "port": 80, "trust_level": "PUBLIC"},
            "service_a": {"role": "Telemetry Agent", "port": 8081, "trust_level": "LOW_TRUST", "spiffe_id": "spiffe://latveria.citadel/sa/telemetry-agent"},
            "service_b": {"role": "Core Controller", "port": 8082, "trust_level": "HIGH_PRIVILEGE", "spiffe_id": "spiffe://latveria.citadel/sa/core-controller"},
            "admin": {"role": "Sovereign Vault Mainframe", "port": 8083, "trust_level": "SOVEREIGN_ROOT", "spiffe_id": "spiffe://latveria.citadel/sa/admin-vault"}
        }
    })


# Proxy routes for Service A (Telemetry & Diagnostics)
@app.route("/api/v1/telemetry/<path:subpath>", methods=["GET", "POST"])
def proxy_telemetry(subpath):
    return forward_to_internal(INTERNAL_ROUTES["service_a"], f"/api/v1/telemetry/{subpath}")


@app.route("/api/v1/diagnostics/<path:subpath>", methods=["GET", "POST"])
def proxy_diagnostics(subpath):
    return forward_to_internal(INTERNAL_ROUTES["service_a"], f"/api/v1/diagnostics/{subpath}")


# Proxy routes for Service B (Core Controller)
@app.route("/api/v1/core/<path:subpath>", methods=["GET", "POST"])
def proxy_core(subpath):
    return forward_to_internal(INTERNAL_ROUTES["service_b"], f"/api/v1/core/{subpath}")


# Proxy routes for Admin Vault
@app.route("/api/v1/admin/<path:subpath>", methods=["GET", "POST"])
def proxy_admin(subpath):
    return forward_to_internal(INTERNAL_ROUTES["admin"], f"/api/v1/admin/{subpath}")


# Generic mesh dispatch router
@app.route("/api/v1/mesh/dispatch", methods=["POST"])
def mesh_dispatch():
    data = request.get_json(silent=True) or {}
    service = data.get("service")
    path = data.get("path", "/")
    if service not in INTERNAL_ROUTES:
        return jsonify({"status": "ERROR", "error": f"Unknown service: {service}"}), 400
    return forward_to_internal(INTERNAL_ROUTES[service], path)


@app.route("/api/v1/reset", methods=["POST"])
def reset():
    reset_mesh_state()
    return jsonify({"status": "RESET_COMPLETE", "timestamp": time.time()})


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "OK", "challenge": "Microservice Trust"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK", "challenge": "Microservice Trust"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    print(f"[*] Starting Public Ingress Gateway on 0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port)
