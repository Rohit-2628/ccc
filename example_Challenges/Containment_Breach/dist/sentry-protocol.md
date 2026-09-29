# Sentinel IPC Telemetry Protocol Specification (v1.0)

## Overview
The Sentinel telemetry daemon (`sentry-agent`) facilitates telemetry ingestion, automated crash snapshots, and health logging.
It operates over a local UNIX domain socket.

## Endpoint
- **Socket Path:** `/run/sentinel/sentry.sock`
- **Socket Permissions:** `0660 (sentry:sentinel-users)`
- **Transport:** Streaming UNIX Domain Socket (`AF_UNIX`, `SOCK_STREAM`)

## Authentication
Every request must include the local service authentication token.
- **Token Location:** `/var/run/sentinel/sentry.token`
- **Permissions:** Mode `0440`, readable by members of the `sentinel-users` group.

## Protocol Commands

### 1. `ping`
Heartbeat check.
```json
{
  "auth_token": "<token>",
  "action": "ping"
}
```

### 2. `status`
Returns daemon status and directory configuration.
```json
{
  "auth_token": "<token>",
  "action": "status"
}
```

### 3. `save_snapshot`
Archives a diagnostic log or snapshot report.
```json
{
  "auth_token": "<token>",
  "action": "save_snapshot",
  "filename": "snapshot_report.log",
  "data": "Raw log data or base64 encoded payload",
  "base64": false
}
```
*Note: Target files are archived into the telemetry store with mode `0600`.*
