#!/usr/bin/env python3
"""
Sentinel Restricted Diagnostics & Telemetry Shell (v2.4)
Stage 1: Enterprise Container Restricted Shell
"""

import sys
import os
import ast
import math
import shlex
import subprocess

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║         SENTINEL SECURE CONTAINER ENVIRONMENT (v2.4)          ║
║      Restricted Diagnostics & Telemetry Interface Shell       ║
╚═══════════════════════════════════════════════════════════════╝
Type 'help' for available commands.
"""

FORBIDDEN_NAMES = {
    'os', 'sys', 'subprocess', 'open', 'eval', 'exec', 'system',
    'popen', 'spawn', 'posix', '__import__', 'breakpoint', 'getattr', 'setattr'
}

SAFE_AST_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name,
    ast.Call, ast.Attribute, ast.Load, ast.Store, ast.List, ast.Tuple, ast.Dict,
    ast.Subscript, ast.Slice, ast.Compare, ast.BoolOp, ast.ListComp,
    ast.comprehension, ast.IfExp, ast.operator, ast.cmpop, ast.boolop
)

def evaluate_alert_rule(expr_str: str):
    """
    Evaluates metric alert expressions using strict AST validation.
    Enforces restricted builtins.
    """
    try:
        parsed = ast.parse(expr_str, mode='eval')
    except Exception as e:
        print(f"[-] Syntax Error in alert expression: {e}")
        return

    # Validate AST nodes
    for node in ast.walk(parsed):
        if not isinstance(node, SAFE_AST_NODES):
            print(f"[-] Security Violation: Forbidden syntax construct '{type(node).__name__}'.")
            return
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            print(f"[-] Security Violation: Identifier '{node.id}' is restricted.")
            return

    # Sandboxed execution environment
    safe_globals = {
        '__builtins__': None,
        'math': math,
        'abs': abs,
        'len': len,
        'str': str,
        'list': list,
        'dict': dict,
        'chr': chr,
        'ord': ord,
        'bytes': bytes,
        'tuple': tuple,
        'int': int,
        'float': float,
        'bool': bool,
    }

    try:
        compiled = compile(parsed, '<alert-rule>', 'eval')
        result = eval(compiled, safe_globals)
        print(f"[+] Alert Rule Evaluation: {result}")
    except Exception as e:
        print(f"[-] Evaluation Error: {e}")

def cmd_status():
    print("[*] Container Telemetry Summary:")
    print("    - State: RUNNING (Isolated Pod)")
    print("    - Host Isolation: cgroups v2 / seccomp active")
    print("    - Internal Services: sentry-agent.service (ONLINE)")
    print("    - IPC Socket: /run/sentinel/sentry.sock (ACTIVE)")

def cmd_read_log(args):
    target = args[0] if args else "system"
    allowed = {"system": "/var/log/sentinel/system.log", "auth": "/var/log/sentinel/auth.log"}
    if target not in allowed:
        print(f"[-] Unknown log target '{target}'. Allowed: system, auth")
        return
    log_file = allowed[target]
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            print(f.read())
    else:
        print(f"[*] Log buffer empty: {log_file}")

def main():
    print(BANNER)
    while True:
        try:
            line = input("sentinel:~$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[+] Exiting Sentinel Shell.")
            break

        if not line:
            continue

        parts = shlex.split(line)
        cmd = parts[0]
        args = parts[1:]

        if cmd == "help":
            print("Available Sentinel Commands:")
            print("  status                   - Display container state and telemetry")
            print("  read-log <system|auth>   - Read sanitized diagnostic log stream")
            print("  eval-rule <expression>   - Evaluate container metric alert rule expression")
            print("  exit / quit              - Terminate diagnostic session")
        elif cmd == "status":
            cmd_status()
        elif cmd == "read-log":
            cmd_read_log(args)
        elif cmd == "eval-rule":
            if not args:
                print("Usage: eval-rule <expression>")
            else:
                expr = " ".join(args)
                evaluate_alert_rule(expr)
        elif cmd in ("exit", "quit"):
            print("[+] Session closed.")
            break
        else:
            print(f"[-] Unknown command: '{cmd}'. Type 'help' for valid commands.")

if __name__ == "__main__":
    main()
