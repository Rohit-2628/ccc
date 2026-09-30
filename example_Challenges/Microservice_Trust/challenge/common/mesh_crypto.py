#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Cryptographic Identity & PKI Framework
Manages challenge-local Root CA, Service-A intermediate credentials,
and certificate chain validation for microservice identity assertions.
"""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import tempfile
import time
from typing import Dict, List, Optional, Tuple

PKI_DIR = os.environ.get("PKI_DIR", "/tmp/citadel_mesh_pki")
CA_KEY_PATH = os.path.join(PKI_DIR, "ca.key")
CA_CRT_PATH = os.path.join(PKI_DIR, "ca.crt")
SERVICE_A_KEY_PATH = os.path.join(PKI_DIR, "service-a.key")
SERVICE_A_CRT_PATH = os.path.join(PKI_DIR, "service-a.crt")

# Shared ticket storage across internal loopback services
TICKET_STORE: Dict[str, dict] = {}


def ensure_pki_initialized():
    """Initializes challenge-local Root CA and Service A credentials safely."""
    os.makedirs(PKI_DIR, exist_ok=True)

    # 1. Initialize Root CA
    if not (os.path.exists(CA_KEY_PATH) and os.path.exists(CA_CRT_PATH)):
        tmp_ca_key = f"{CA_KEY_PATH}.tmp.{os.getpid()}"
        tmp_ca_crt = f"{CA_CRT_PATH}.tmp.{os.getpid()}"
        try:
            subprocess.run([
                "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                "-keyout", tmp_ca_key, "-out", tmp_ca_crt, "-days", "3650",
                "-subj", "/CN=Latveria Citadel Root CA/O=Latverian Defense Network/OU=Security Operations"
            ], check=True, capture_output=True)
            if not os.path.exists(CA_KEY_PATH):
                os.rename(tmp_ca_key, CA_KEY_PATH)
            if not os.path.exists(CA_CRT_PATH):
                os.rename(tmp_ca_crt, CA_CRT_PATH)
        except Exception:
            pass
        finally:
            if os.path.exists(tmp_ca_key):
                os.remove(tmp_ca_key)
            if os.path.exists(tmp_ca_crt):
                os.remove(tmp_ca_crt)

    # 2. Initialize Service A (telemetry-agent) certificate
    # Intentionally issued with BasicConstraints: CA:TRUE (The flawed trust assumption)
    if not (os.path.exists(SERVICE_A_KEY_PATH) and os.path.exists(SERVICE_A_CRT_PATH)):
        pid = os.getpid()
        sa_key_tmp = f"{SERVICE_A_KEY_PATH}.tmp.{pid}"
        sa_csr_tmp = f"{PKI_DIR}/sa.csr.{pid}"
        sa_ext_tmp = f"{PKI_DIR}/sa.ext.{pid}"
        sa_crt_tmp = f"{SERVICE_A_CRT_PATH}.tmp.{pid}"

        try:
            with open(sa_ext_tmp, "w") as f:
                f.write("basicConstraints = CA:TRUE, pathlen:1\n")
                f.write("keyUsage = digitalSignature, keyEncipherment, keyCertSign\n")
                f.write("subjectAltName = URI:spiffe://latveria.citadel/sa/telemetry-agent, DNS:telemetry-agent.latveria.local\n")

            subprocess.run([
                "openssl", "req", "-newkey", "rsa:2048", "-nodes",
                "-keyout", sa_key_tmp, "-out", sa_csr_tmp,
                "-subj", "/CN=telemetry-agent.latveria.local/O=Latverian Defense Network/OU=Edge Telemetry"
            ], check=True, capture_output=True)

            subprocess.run([
                "openssl", "x509", "-req", "-in", sa_csr_tmp, "-CA", CA_CRT_PATH, "-CAkey", CA_KEY_PATH,
                "-CAcreateserial", "-out", sa_crt_tmp, "-days", "365",
                "-extfile", sa_ext_tmp
            ], check=True, capture_output=True)

            if not os.path.exists(SERVICE_A_KEY_PATH):
                os.rename(sa_key_tmp, SERVICE_A_KEY_PATH)
            if not os.path.exists(SERVICE_A_CRT_PATH):
                os.rename(sa_crt_tmp, SERVICE_A_CRT_PATH)
        except Exception:
            pass
        finally:
            for p in [sa_key_tmp, sa_csr_tmp, sa_ext_tmp, sa_crt_tmp]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass


def get_ca_cert_pem() -> str:
    ensure_pki_initialized()
    with open(CA_CRT_PATH, "r") as f:
        return f.read()


def get_service_a_cert_pem() -> str:
    ensure_pki_initialized()
    with open(SERVICE_A_CRT_PATH, "r") as f:
        return f.read()


def get_service_a_key_pem() -> str:
    ensure_pki_initialized()
    with open(SERVICE_A_KEY_PATH, "r") as f:
        return f.read()


def split_pem_certificates(pem_bundle: str) -> List[str]:
    """Splits a multi-certificate PEM string into individual certificate PEM blocks."""
    certs = []
    current = []
    for line in pem_bundle.strip().splitlines():
        if "-----BEGIN CERTIFICATE-----" in line:
            current = [line]
        elif "-----END CERTIFICATE-----" in line:
            current.append(line)
            certs.append("\n".join(current))
            current = []
        elif current:
            current.append(line)
    return certs


def parse_certificate_identity(cert_pem: str) -> Dict[str, any]:
    """Extracts Subject CN and Subject Alternative Names (SANs) from a PEM certificate."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False) as f:
        f.write(cert_pem)
        cert_file = f.name

    try:
        # Extract Subject
        sub_res = subprocess.run(
            ["openssl", "x509", "-in", cert_file, "-noout", "-subject"],
            capture_output=True, text=True, check=True
        )
        subject = sub_res.stdout.strip()
        cn_match = re.search(r"CN\s*=\s*([^/,\n]+)", subject)
        cn = cn_match.group(1).strip() if cn_match else ""

        # Extract Extensions (SANs)
        ext_res = subprocess.run(
            ["openssl", "x509", "-in", cert_file, "-noout", "-ext", "subjectAltName"],
            capture_output=True, text=True
        )
        sans = []
        spiffe_id = None
        for line in ext_res.stdout.splitlines():
            line = line.strip()
            if "URI:spiffe://" in line or "DNS:" in line or "IP Address:" in line or "URI:" in line:
                for part in line.split(","):
                    p = part.strip()
                    sans.append(p)
                    if p.startswith("URI:spiffe://"):
                        spiffe_id = p[4:]  # remove URI: prefix

        return {
            "subject": subject,
            "cn": cn,
            "sans": sans,
            "spiffe_id": spiffe_id or (f"spiffe://latveria.citadel/sa/{cn}" if cn else None)
        }
    except Exception as e:
        return {"error": str(e), "subject": "", "cn": "", "sans": [], "spiffe_id": None}
    finally:
        if os.path.exists(cert_file):
            os.remove(cert_file)


def verify_mesh_identity_cert(cert_data: str) -> Tuple[bool, str, Dict[str, any]]:
    """
    Verifies a client certificate chain against Citadel Root CA.
    The cert_data can be:
    - A single leaf PEM certificate
    - A concatenated PEM certificate bundle (leaf cert + untrusted intermediate certs)
    - Base64 encoded PEM certificate / bundle
    - URL-encoded PEM certificate
    """
    ensure_pki_initialized()

    # Clean and decode input
    cert_pem_str = cert_data.strip()
    if cert_pem_str.startswith("%2D%2D%2D") or "%20" in cert_pem_str:
        import urllib.parse
        cert_pem_str = urllib.parse.unquote(cert_pem_str)

    if not ("-----BEGIN CERTIFICATE-----" in cert_pem_str):
        try:
            decoded = base64.b64decode(cert_pem_str).decode("utf-8", errors="ignore")
            if "-----BEGIN CERTIFICATE-----" in decoded:
                cert_pem_str = decoded
        except Exception:
            pass

    if "-----BEGIN CERTIFICATE-----" not in cert_pem_str:
        return False, "Invalid certificate format. Expected PEM block with -----BEGIN CERTIFICATE-----", {}

    certs = split_pem_certificates(cert_pem_str)
    if not certs:
        return False, "No valid PEM certificates found in provided identity header", {}

    leaf_cert_pem = certs[0]
    intermediate_pems = certs[1:]

    # Write files for OpenSSL verification
    with tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False) as leaf_f:
        leaf_f.write(leaf_cert_pem)
        leaf_path = leaf_f.name

    untrusted_path = None
    if intermediate_pems:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".crt", delete=False) as untrusted_f:
            untrusted_f.write("\n".join(intermediate_pems))
            untrusted_path = untrusted_f.name

    try:
        verify_cmd = ["openssl", "verify", "-CAfile", CA_CRT_PATH]
        if untrusted_path:
            verify_cmd.extend(["-untrusted", untrusted_path])
        verify_cmd.append(leaf_path)

        res = subprocess.run(verify_cmd, capture_output=True, text=True)

        if res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip()
            return False, f"Certificate verification failed: {err_msg}", {}

        identity_info = parse_certificate_identity(leaf_cert_pem)
        return True, "Certificate verified successfully", identity_info

    except Exception as e:
        return False, f"Verification execution error: {str(e)}", {}
    finally:
        if os.path.exists(leaf_path):
            os.remove(leaf_path)
        if untrusted_path and os.path.exists(untrusted_path):
            os.remove(untrusted_path)


TICKETS_FILE = os.path.join(PKI_DIR, "tickets.json")


def _load_tickets() -> dict:
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_tickets(tickets: dict):
    tmp = f"{TICKETS_FILE}.tmp.{os.getpid()}"
    try:
        with open(tmp, "w") as f:
            json.dump(tickets, f)
        os.rename(tmp, TICKETS_FILE)
    except Exception:
        pass
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def issue_admin_ticket(identity_info: Dict[str, any]) -> str:
    """Issues a time-limited Admin Ticket for authorized service identities."""
    ticket_id = f"LATV-ADMIN-TICKET-{secrets.token_hex(16).upper()}"
    ticket_data = {
        "ticket": ticket_id,
        "issued_at": time.time(),
        "expires_at": time.time() + 3600,
        "identity": identity_info.get("spiffe_id") or identity_info.get("cn"),
        "cn": identity_info.get("cn"),
        "role": "SOVEREIGN_ADMIN"
    }
    
    tickets = _load_tickets()
    tickets[ticket_id] = ticket_data
    _save_tickets(tickets)
    TICKET_STORE[ticket_id] = ticket_data
    return ticket_id


def validate_admin_ticket(ticket_id: str) -> Tuple[bool, str, Optional[dict]]:
    """Validates an Admin Ticket."""
    if not ticket_id:
        return False, "Missing Admin Ticket", None

    tickets = _load_tickets()
    ticket = tickets.get(ticket_id.strip())
    if not ticket:
        return False, "Invalid or unrecognized Admin Ticket", None

    if time.time() > ticket.get("expires_at", 0):
        return False, "Admin Ticket has expired", None

    return True, "Valid ticket", ticket


def reset_mesh_state():
    """Resets ephemeral tickets and reinitializes PKI state."""
    TICKET_STORE.clear()
    if os.path.exists(TICKETS_FILE):
        try:
            os.remove(TICKETS_FILE)
        except OSError:
            pass
    ensure_pki_initialized()
