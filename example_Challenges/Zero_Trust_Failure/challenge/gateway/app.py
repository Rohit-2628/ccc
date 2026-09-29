#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Public Gateway & Ingress Orchestrator
Challenge: X10 — Zero Trust Failure
Port: 0.0.0.0:80
Routes external player traffic to the Low-Trust Application.
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
from common.mesh_identity import ensure_mesh_initialized, reset_mesh_state

app = Flask(__name__)
ensure_mesh_initialized()

LOW_TRUST_URL = "http://127.0.0.1:8081"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Latverian Citadel — Zero-Trust Network Fabric</title>
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-tertiary: #1f293d;
            --accent-green: #10b981;
            --accent-emerald: #059669;
            --accent-red: #ef4444;
            --accent-amber: #f59e0b;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --border-color: #2e3a52;
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
            background: linear-gradient(135deg, var(--accent-emerald), var(--accent-cyan));
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

        @media (max-width: 960px) {
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

        .topology-node.low-trust { border-left-color: var(--accent-amber); }
        .topology-node.trusted { border-left-color: var(--accent-purple); }
        .topology-node.admin-vault { border-left-color: var(--accent-red); }

        .node-info h4 { font-size: 14px; margin-bottom: 2px; }
        .node-info p { font-size: 12px; color: var(--text-muted); font-family: var(--font-mono); }

        .badge {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }

        .badge-ingress { background: rgba(6, 182, 212, 0.2); color: var(--accent-cyan); }
        .badge-low { background: rgba(245, 158, 11, 0.2); color: var(--accent-amber); }
        .badge-trusted { background: rgba(139, 92, 246, 0.2); color: var(--accent-purple); }
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
            max-height: 280px;
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

        .btn:hover { opacity: 0.9; }

        .btn-outline {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-main);
        }

        .form-group { margin-bottom: 12px; }

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
            <span class="brand-badge">CITADEL ZERO</span>
            <h1>Zero-Trust Mesh Gateway Console (X10)</h1>
        </div>
        <div class="status-pill">
            <div class="status-dot"></div>
            <span>INGRESS ACTIVE [TCP/80]</span>
        </div>
    </header>

    <div class="grid">
        <!-- Topology View -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Masterbook Architecture & Trust Flow</span>
            </div>
            
            <div class="topology-node">
                <div class="node-info">
                    <h4>Public Gateway</h4>
                    <p>Interface: TCP/80 (External Ingress Proxy)</p>
                </div>
                <span class="badge badge-ingress">GATEWAY</span>
            </div>

            <div style="text-align: center; color: var(--text-muted); margin: -4px 0 8px 0;">▼ routes public player requests</div>

            <div class="topology-node low-trust">
                <div class="node-info">
                    <h4>Low-Trust Application</h4>
                    <p>Internal: 127.0.0.1:8081 | Edge Worker (Diagnostics & Relay)</p>
                </div>
                <span class="badge badge-low">LOW TRUST</span>
            </div>

            <div style="text-align: center; color: var(--text-muted); margin: -4px 0 8px 0;">▼ intended service trust boundary (X-Citadel-Assertion)</div>

            <div class="topology-node trusted">
                <div class="node-info">
                    <h4>Trusted Internal Service</h4>
                    <p>Internal: 127.0.0.1:8082 | Citadel Core Policy Engine</p>
                </div>
                <span class="badge badge-trusted">TRUSTED CORE</span>
            </div>

            <div style="text-align: center; color: var(--text-muted); margin: -4px 0 8px 0;">▼ Admin Grant Ticket (LATV-ADMIN-PASS-*)</div>

            <div class="topology-node admin-vault">
                <div class="node-info">
                    <h4>Admin Service — Citadel Sovereign Vault</h4>
                    <p>Internal: 127.0.0.1:8083 | Protected Flag Custodian</p>
                </div>
                <span class="badge badge-admin">SOVEREIGN ROOT</span>
            </div>
        </div>

        <!-- Interactive API Studio -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">Gateway Command Console</span>
            </div>

            <div class="form-group">
                <label>HTTP Method & Target Route</label>
                <div style="display: flex; gap: 8px;">
                    <select id="reqMethod" style="width: 100px;">
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                    </select>
                    <input type="text" id="reqPath" value="/api/v1/telemetry/status" placeholder="/api/v1/...">
                </div>
            </div>

            <div class="form-group">
                <label>JSON Request Body</label>
                <textarea id="reqBody" rows="3" placeholder='{"script": "print(open(\\"/tmp/citadel_mesh_state/mesh_config.json\\").read())"}'></textarea>
            </div>

            <div style="display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">
                <button class="btn" onclick="sendMeshRequest()">Send Request</button>
                <button class="btn btn-outline" onclick="loadSample('telemetry')">Sample: Telemetry</button>
                <button class="btn btn-outline" onclick="loadSample('inspect')">Sample: Inspect</button>
                <button class="btn btn-outline" onclick="loadSample('exec')">Sample: Exec Script</button>
            </div>

            <label>Response Console</label>
            <div id="responseConsole" class="code-block">Waiting for request dispatch...</div>
        </div>
    </div>

    <div style="margin-top: 24px;" class="card">
        <div class="card-header">
            <span class="card-title">Exposed Gateway Interface Reference</span>
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; font-family: var(--font-mono);">
            <thead>
                <tr style="text-align: left; border-bottom: 1px solid var(--border-color); color: var(--accent-cyan);">
                    <th style="padding: 8px;">Public Path</th>
                    <th style="padding: 8px;">Proxied Internal Component</th>
                    <th style="padding: 8px;">Description</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px; color: var(--accent-green);">GET /api/v1/telemetry/status</td>
                    <td style="padding: 8px;">Low-Trust App (:8081)</td>
                    <td style="padding: 8px;">Edge worker health & telemetry</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px; color: var(--accent-green);">GET /api/v1/diagnostics/inspect</td>
                    <td style="padding: 8px;">Low-Trust App (:8081)</td>
                    <td style="padding: 8px;">Diagnostic inspection & attestation metadata</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px; color: var(--accent-amber);">POST /api/v1/diagnostics/exec</td>
                    <td style="padding: 8px;">Low-Trust App (:8081)</td>
                    <td style="padding: 8px;">Diagnostic execution console in low-trust sandbox</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: var(--accent-purple);">POST /api/v1/relay/dispatch</td>
                    <td style="padding: 8px;">Low-Trust App (:8081)</td>
                    <td style="padding: 8px;">Internal mesh dispatcher with custom assertion headers</td>
                </tr>
            </tbody>
        </table>
    </div>

    <script>
        function loadSample(type) {
            const method = document.getElementById('reqMethod');
            const path = document.getElementById('reqPath');
            const body = document.getElementById('reqBody');

            if (type === 'telemetry') {
                method.value = 'GET';
                path.value = '/api/v1/telemetry/status';
                body.value = '';
            } else if (type === 'inspect') {
                method.value = 'GET';
                path.value = '/api/v1/diagnostics/inspect';
                body.value = '';
            } else if (type === 'exec') {
                method.value = 'POST';
                path.value = '/api/v1/diagnostics/exec';
                body.value = JSON.stringify({
                    script: "import json\\nconfig = get_mesh_config()\\nprint(json.dumps(config, indent=2))"
                }, null, 2);
            }
        }

        async function sendMeshRequest() {
            const method = document.getElementById('reqMethod').value;
            const path = document.getElementById('reqPath').value;
            const bodyRaw = document.getElementById('reqBody').value;
            const consoleEl = document.getElementById('responseConsole');

            consoleEl.innerText = 'Routing request via Gateway to ' + path + '...';

            try {
                const options = {
                    method: method,
                    headers: {}
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
                consoleEl.innerText = `[Gateway Dispatch Error]\\n` + err.message;
            }
        }
    </script>
</body>
</html>
"""


def forward_to_low_trust(path_suffix: str):
    """Proxy request to internal low-trust service on 127.0.0.1:8081."""
    target_url = f"{LOW_TRUST_URL}{path_suffix}"
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
        with urllib.request.urlopen(req, timeout=10) as response:
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
            "message": f"Failed to contact Low-Trust Service at {target_url}: {str(e)}"
        }), 502


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/v1/topology", methods=["GET"])
def topology():
    return jsonify({
        "challenge_id": "X10",
        "challenge_name": "Zero Trust Failure",
        "mesh_fabric": "Citadel Zero Trust Mesh",
        "gateway_interface": "TCP/80",
        "pipeline": "Player -> Gateway -> Low-Trust App -> Trusted Internal Service -> Admin -> Flag",
        "components": {
            "gateway": {"role": "Public Ingress Proxy", "port": 80, "visibility": "PUBLIC"},
            "low_trust_app": {"role": "Edge Diagnostics & Relay", "port": 8081, "visibility": "INTERNAL_LOOPBACK", "trust": "LOW"},
            "trusted_service": {"role": "Citadel Core Policy Engine", "port": 8082, "visibility": "INTERNAL_LOOPBACK", "trust": "HIGH"},
            "admin_service": {"role": "Citadel Sovereign Vault", "port": 8083, "visibility": "INTERNAL_LOOPBACK", "trust": "SOVEREIGN_ROOT"}
        }
    })


# Proxy all Low-Trust App endpoints
@app.route("/api/v1/telemetry/<path:subpath>", methods=["GET", "POST"])
def proxy_telemetry(subpath):
    return forward_to_low_trust(f"/api/v1/telemetry/{subpath}")


@app.route("/api/v1/diagnostics/<path:subpath>", methods=["GET", "POST"])
def proxy_diagnostics(subpath):
    return forward_to_low_trust(f"/api/v1/diagnostics/{subpath}")


@app.route("/api/v1/relay/<path:subpath>", methods=["GET", "POST"])
def proxy_relay(subpath):
    return forward_to_low_trust(f"/api/v1/relay/{subpath}")


# Direct external calls to core or admin are blocked by Gateway (must go through Low-Trust App)
@app.route("/api/v1/core/<path:subpath>", methods=["GET", "POST"])
def block_direct_core(subpath):
    return jsonify({
        "status": "FORBIDDEN",
        "error": "DirectAccessBlocked",
        "message": "Direct external access to Trusted Internal Service is blocked by Gateway Network Policy. Requests must traverse the internal service pipeline."
    }), 403


@app.route("/api/v1/admin/<path:subpath>", methods=["GET", "POST"])
def block_direct_admin(subpath):
    return jsonify({
        "status": "FORBIDDEN",
        "error": "DirectAccessBlocked",
        "message": "Direct external access to Admin Sovereign Vault is blocked by Gateway Network Policy."
    }), 403


@app.route("/api/v1/reset", methods=["POST"])
def reset():
    reset_mesh_state()
    return jsonify({"status": "RESET_COMPLETE", "timestamp": time.time()})


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "OK", "service": "gateway"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    print(f"[*] Starting Public Ingress Gateway on 0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port)
