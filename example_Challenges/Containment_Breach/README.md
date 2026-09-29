# Containment Breach: Modular Hard Shell & Container Base Model

## Overview
**Containment Breach** is an enterprise-grade, multi-stage Linux container security challenge engineered as a modular, extensible base platform.
It is designed to serve as both an immediate high-difficulty shell/privesc challenge and a flexible scaffold from which organizers can build additional layers, pivot networks, or alternative exploitation vectors.

---

## Architecture Matrix

| Stage | Subsystem | User Context | Vulnerability Class | Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | Sentinel Diagnostic Shell | `ctf` (uid 1001) | Restricted Shell / AST PyJail | Python Subclass Navigation (`subprocess.Popen`) |
| **Stage 2** | Sentry IPC Telemetry Daemon | `sentry` (uid 1002) | Path Override / Logic Flaw | `os.path.join` absolute path override (`authorized_keys`) |
| **Stage 3** | Container Control Daemon | `root` (uid 0) | SUID Stack Buffer Overflow | Ret2win overwrite of return pointer to `emergency_console` |

---

## Directory Organization

```
Containment_Breach/
├── Dockerfile                  # Production container definition (Ubuntu 22.04 base)
├── entrypoint.sh               # Platform runtime entrypoint & flag manager
├── config/
│   └── sentinel.conf           # Challenge parameters & stage toggles
├── src/
│   ├── sentinel-shell.py       # Stage 1: Restricted shell implementation
│   ├── sentry-agent.py         # Stage 2: IPC domain socket daemon
│   ├── container-ctl.c         # Stage 3: SUID binary source
│   └── Makefile                # Compiler specifications
├── modules/
│   ├── stage1_jail/            # Stage 1 documentation and extension guide
│   ├── stage2_daemon/          # Stage 2 documentation and extension guide
│   └── stage3_privesc/         # Stage 3 documentation and extension guide
├── dist/                       # Clean participant distribution bundle (zero leaks)
│   ├── Dockerfile              # Participant local test build file
│   ├── README.md               # Challenge briefing
│   ├── container-ctl.c         # SUID source code for white-box auditing
│   └── sentry-protocol.md      # IPC protocol specification
├── solve.py                    # Deterministic end-to-end exploit solver
└── solution.md                 # Complete organizer walkthrough & writeup
```

---

## How to Build & Extend From This Base Model

The architecture was intentionally designed for modular expansion:

### 1. Swapping or Bypassing Stages
- To grant direct bash access and bypass Stage 1, set `ENABLE_RESTRICTED_SHELL=false` in `config/sentinel.conf` or change the user shell in `entrypoint.sh`.
- To swap Stage 1 with a restricted bash (`rbash`) or a C chroot environment, replace `sentinel-shell.py` with your implementation.

### 2. Modifying Stage 2 Vulnerabilities
- Currently, `sentry-agent.py` demonstrates an absolute path override vulnerability.
- You can easily extend it to demonstrate:
  - Insecure deserialization (`pickle.loads` or `yaml.load(UnsafeLoader)`).
  - Shell command injection via an unquoted parameter in snapshot archiving.
  - Race conditions (TOCTOU) when validating file ownership.

### 3. Modifying Stage 3 Privilege Escalation
- `container-ctl.c` comes with both a stack buffer overflow in `--load-diag` and a format string vulnerability in `--log-event`.
- You can enable ASLR / PIE for ROP chains, or replace it with a Linux capability challenge (e.g. `CAP_DAC_READ_SEARCH`, `CAP_SYS_PTRACE`).

### 4. Adding a Stage 4 (Container Escape or Lateral Cluster Movement)
- Add a simulated Kubernetes microservice endpoint or container escape scenario.
- In sandbox environments, connect this container to an isolated internal subnet with a secondary target node.

---

## Testing & Verification
Build and run the container locally:
```bash
docker build -t containment-breach .
docker run -d --name test-sentinel -p 2222:22 containment-breach
```

Run the automated solver:
```bash
python3 solve.py --host 127.0.0.1 --port 2222 --user ctf --password sentinel123
```
