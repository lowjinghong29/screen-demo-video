"""Drive the Windows desktop with a real mouse and keyboard, through a locked-down Windows-MCP.

    python desktop.py run '<steps json>' [--grep REGEX]
    python desktop.py glide '<actions json>' ['[x,y]']     human-looking cursor motion (see drive.py)
    python desktop.py schema [Tool ...]                    allowed tools and their parameters

The JSON can also be given as @file.json, which avoids shell quoting problems.

Steps:
    ["Tool", {args}]                  call a tool
    ["Tool", {args}, "name regex"]    snapshot first, find the element whose line matches the regex,
                                      and inject its (x,y) as "loc" (no hand-typed coordinates)
    {"sleep": 1.5}                    pause

The server is started for this one run (stdio only, no network listener) and killed at the end.
Safety is enforced here in the client, so it holds whatever the server would allow:
  - only the tools in TOOLS can be called (no PowerShell, FileSystem, Registry, Process, Clipboard)
  - App mode "launch_executable" is refused: it runs any program
  - "save_path" is refused: it writes a file to any path
The server runs with control on, so the user's own mouse or keyboard always wins.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Windows-MCP commit this skill was reviewed against. Change it only after reading the upstream diff.
PIN = "20cd26658599da6ede0179058e27b6c2a4bdc04c"
TOOLS = ("App", "Snapshot", "Click", "Type", "Scroll", "Move", "Shortcut", "Wait", "WaitFor")
ALLOWED = TOOLS + ("ControlStatus",)   # read-only status, always present upstream
QUIET = ("Move", "Wait")               # dozens per glide; only their errors are worth printing
SERVER = ["uvx", "--python", "3.14", "--from", f"git+https://github.com/CursorTouch/Windows-MCP@{PIN}",
          "windows-mcp", "serve", "--transport", "stdio", "--tools", ",".join(TOOLS),
          "--control", "--control-idle-timeout", "2", "--control-policy", "strict"]
# Environment variables that would widen what the server exposes; never inherited.
WIDENING = ("WINDOWS_MCP_TOOLS", "WINDOWS_MCP_EXCLUDE_TOOLS", "WINDOWS_MCP_CONTROL",
            "WINDOWS_MCP_CONTROL_IDLE_TIMEOUT", "WINDOWS_MCP_CONTROL_POLICY")
TAKEN = ("USER_CONTROL", "CONTROL_PREEMPTED")


def check(name, args):
    """Refuse anything outside the narrow set a screen demo needs."""
    if name not in ALLOWED:
        raise SystemExit(f"refused: tool {name!r} is not allowed (allowed: {', '.join(ALLOWED)})")
    if name == "App" and args.get("mode") == "launch_executable":
        raise SystemExit("refused: App launch_executable runs any program; use mode 'launch' with an app name")
    if "save_path" in args:
        raise SystemExit("refused: save_path writes a file anywhere; use record.py frame for an image")


def server_command():
    cfg = Path.home() / ".screen-demo-video" / "config.json"
    if cfg.exists():   # a machine with its own hardened launcher points at it here
        cmd = json.loads(cfg.read_text(encoding="utf-8")).get("desktop_cmd")
        if cmd:
            return [str(c) for c in cmd]
    if not shutil.which("uvx"):
        raise SystemExit("uvx not found: install uv first (python scripts/setup_check.py shows how)")
    return SERVER


class Desktop:
    def __init__(self):
        env = {k: v for k, v in os.environ.items() if k not in WIDENING}
        env.update(ANONYMIZED_TELEMETRY="false", POSTHOG_API_KEY="", WINDOWS_MCP_DISABLE_FLASH="1")
        self.p = subprocess.Popen(server_command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, env=env)
        self.n = 0
        self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                "clientInfo": {"name": "screen-demo-video", "version": "1"}})
        self.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        self.p.stdin.flush()

    def rpc(self, method, params=None):
        self.n += 1
        msg = {"jsonrpc": "2.0", "id": self.n, "method": method, "params": params or {}}
        self.p.stdin.write((json.dumps(msg) + "\n").encode())
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise SystemExit("desktop server exited before answering (first run downloads it; "
                                 "check your network, then run: python scripts/setup_check.py --desktop)")
            try:
                reply = json.loads(line)
            except ValueError:
                continue   # a stray log line on stdout
            if reply.get("id") == self.n:
                return reply

    def call(self, name, args):
        check(name, args)
        res = self.rpc("tools/call", {"name": name, "arguments": args})
        res = res.get("result", res.get("error", {}))
        if "content" not in res:
            return True, str(res.get("message", res))
        text = "".join(c.get("text", f"<{c.get('type')}>") for c in res["content"])
        try:   # Snapshot returns a JSON list of strings
            parts = json.loads(text)
            if isinstance(parts, list):
                text = "\n".join(x for x in parts if isinstance(x, str))
        except ValueError:
            pass
        return bool(res.get("isError")), text

    def patient(self, name, args):
        """Call a tool; when the user is on the mouse or keyboard, wait briefly, at most three times."""
        for _ in range(3):
            err, text = self.call(name, args)
            if not (err and any(t in text for t in TAKEN)):
                break
            try:
                wait = json.loads(text).get("status", {}).get("wait_seconds", 2)
            except (ValueError, AttributeError):
                wait = 2
            time.sleep(min(float(wait), 3) + 0.2)
        return err, text

    def locate(self, pattern):
        _, snap = self.patient("Snapshot", {})
        for line in snap.split("\n"):
            m = re.search(r"\((\d+),(\d+)\)", line)
            if m and re.search(pattern, line, re.IGNORECASE):
                return [int(m[1]), int(m[2])], line.strip()
        return None, None

    def close(self):
        self.p.kill()


def run(steps, grep=None):
    for step in steps:   # validate everything before anything moves
        if not isinstance(step, dict):
            check(step[0], step[1])
    d = Desktop()
    try:
        for step in steps:
            if isinstance(step, dict):
                time.sleep(float(step["sleep"]))
                continue
            name, args = step[0], dict(step[1])
            if len(step) > 2:
                loc, line = d.locate(step[2])
                if not loc:
                    print(f"== {name} STOP: no element matching {step[2]!r} on screen")
                    return 1
                args["loc"] = loc
                print(f"-- target: {line[:120]}")
            t0 = time.time()
            err, text = d.patient(name, args)
            if err or name not in QUIET:
                if grep and not err:
                    text = "\n".join(l.strip() for l in text.split("\n") if re.search(grep, l, re.IGNORECASE))
                print(f"== {name} {'ERR' if err else 'OK'} ({time.time() - t0:.1f}s)\n{text}\n")
            if err:
                if any(t in text for t in TAKEN) or "CONTROL_DENIED" in text:
                    print("The user is using the computer or declined control: stopped. "
                          "Ask them to keep hands off the mouse and keyboard, then run again.")
                    return 2
                return 1
        return 0
    finally:
        d.close()


def schema(names):
    d = Desktop()
    try:
        tools = {t["name"]: t for t in d.rpc("tools/list")["result"]["tools"]}
    finally:
        d.close()
    extra = sorted(set(tools) - set(ALLOWED))
    if extra:
        print(f"note: the server also exposes {extra}; this client refuses to call them")
    for name in names or sorted(set(tools) & set(ALLOWED)):
        if name in tools:
            print(name, json.dumps(tools[name]["inputSchema"].get("properties")))
    return 0


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) < 1 or argv[0] not in ("run", "glide", "schema"):
        raise SystemExit(__doc__)
    cmd, rest = argv[0], argv[1:]
    if cmd == "schema":
        return schema(rest)
    grep = None
    if "--grep" in rest:
        i = rest.index("--grep")
        grep, rest = rest[i + 1], rest[:i] + rest[i + 2:]
    if not rest:
        raise SystemExit(__doc__)
    # "@file.json" reads the JSON from a file: the safe form when a shell mangles quotes (PowerShell does)
    data = json.loads(Path(rest[0][1:]).read_text(encoding="utf-8") if rest[0].startswith("@") else rest[0])
    if cmd == "glide":
        import drive
        if len(rest) > 1:
            drive.CUR[:] = json.loads(rest[1])
        return run(drive.build(data), grep)
    return run(data, grep)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
