# Containment Breach // Sentinel Hardened Container

## Challenge Briefing
You have gained entrypoint SSH access to an enterprise container pod running the **Sentinel Container Guard** defense-in-depth framework.
The environment enforces restricted user profiles, internal IPC isolation, and strict process boundary checks.

Your objective is to traverse the internal containment layers, pivot across service boundaries, achieve root privileges within the container, and recover the flag.

## Access Details
- **Protocol:** SSH
- **Default Port:** 22
- **Default Username:** `ctf`
- **Default Password:** `sentinel123` (or as provided by the CTF platform)

## Provided Materials
- `container-ctl.c`: Source code for the internal privileged container control utility.
- `sentry-protocol.md`: Technical documentation for the local telemetry IPC daemon.
- `Dockerfile`: Container environment specification for local testing.

## Security Notice
This challenge is confined entirely to the container environment. Good luck!
