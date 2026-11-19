"""Start the UniFi Network MCP server and, when configured, the relay.

Every log line is a plain sentence so it reads well with a screen reader.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time

OPTIONS_PATH = os.environ.get("ADDON_OPTIONS_PATH", "/data/options.json")
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 3000
SECRET_DIR = os.environ.get("ADDON_SECRET_DIR", "/tmp")

POLICY_ACTIONS = ("CREATE", "UPDATE", "DELETE")


def say(message: str) -> None:
    print(f"UniFi for Claude: {message}", flush=True)


def stop(message: str, code: int = 1) -> None:
    say(message)
    sys.exit(code)


def load_options() -> dict:
    try:
        with open(OPTIONS_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        stop(f"Settings file not found at {OPTIONS_PATH}.")
    except json.JSONDecodeError as error:
        stop(f"Settings file could not be read: {error}.")
    return {}


def clean_address(value: str) -> str:
    """Accept common typing variants like https://192.168.1.1/ and trim them."""
    value = (value or "").strip()
    for prefix in ("https://", "http://"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
    return value.split("/")[0].strip()


def check_options(opts: dict) -> list[str]:
    problems = []
    if not clean_address(opts.get("router_address", "")):
        problems.append("Router address is empty. Enter your UniFi gateway's IP address, for example 192.168.1.1.")
    if not (opts.get("router_username") or "").strip():
        problems.append("Router username is empty.")
    if not opts.get("router_password"):
        problems.append("Router password is empty.")

    relay_address = (opts.get("relay_address") or "").strip()
    relay_token = (opts.get("relay_token") or "").strip()
    if relay_address and not relay_address.lower().startswith("https://"):
        problems.append("Relay address must start with https://.")
    if bool(relay_address) != bool(relay_token):
        problems.append("Relay address and relay token must both be filled in, or both left empty.")
    return problems


def write_secret(value: str) -> str:
    handle, path = tempfile.mkstemp(prefix="unifi-", dir=SECRET_DIR)
    with os.fdopen(handle, "w", encoding="utf-8") as secret_file:
        secret_file.write(value)
    os.chmod(path, 0o600)
    return path


def server_environment(opts: dict, password_file: str) -> dict:
    env = dict(os.environ)
    allow = "true" if opts.get("allow_changes") else "false"
    env.update(
        {
            "UNIFI_NETWORK_HOST": clean_address(opts["router_address"]),
            "UNIFI_NETWORK_USERNAME": opts["router_username"].strip(),
            "UNIFI_NETWORK_PASSWORD_FILE": password_file,
            "UNIFI_NETWORK_PORT": str(opts.get("router_port") or 443),
            "UNIFI_NETWORK_SITE": (opts.get("site_name") or "default").strip() or "default",
            "UNIFI_NETWORK_VERIFY_SSL": "true" if opts.get("check_router_certificate") else "false",
            # Every change is previewed and needs confirmation, even when allowed.
            "UNIFI_NETWORK_TOOL_PERMISSION_MODE": "confirm",
            # HTTP stays inside this app only; the relay is the sole way in.
            "UNIFI_MCP_HTTP_ENABLED": "true",
            "UNIFI_MCP_HTTP_TRANSPORT": "streamable-http",
            "UNIFI_MCP_HTTP_FORCE": "true",
            # HTTP alone, even though this server is not the container's main process.
            # Needs unifi-mcp-shared 0.6.42 or newer (added for this app, issue 1047).
            "UNIFI_MCP_STDIO_ENABLED": "false",
            "UNIFI_MCP_HOST": SERVER_HOST,
            "UNIFI_MCP_PORT": str(SERVER_PORT),
            "UNIFI_MCP_ALLOWED_HOSTS": "localhost,127.0.0.1",
            "UNIFI_MCP_ENABLE_DNS_REBINDING_PROTECTION": "true",
        }
    )
    for action in POLICY_ACTIONS:
        env[f"UNIFI_POLICY_NETWORK_{action}"] = allow
    if opts.get("detailed_logs"):
        env["UNIFI_MCP_LOG_LEVEL"] = "DEBUG"
    # Never let a stray password variable override the file.
    env.pop("UNIFI_NETWORK_PASSWORD", None)
    env.pop("UNIFI_PASSWORD", None)
    return env


def relay_environment(opts: dict) -> dict:
    env = dict(os.environ)
    env.update(
        {
            "UNIFI_RELAY_URL": opts["relay_address"].strip().rstrip("/"),
            "UNIFI_RELAY_TOKEN": opts["relay_token"].strip(),
            "UNIFI_RELAY_LOCATION_NAME": (opts.get("location_name") or "Home").strip() or "Home",
            "UNIFI_RELAY_SERVERS": f"http://{SERVER_HOST}:{SERVER_PORT}",
        }
    )
    return env


def wait_for_port(host: str, port: int, process: subprocess.Popen, seconds: int) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(1)
    return False


def main() -> None:
    say("Starting.")
    opts = load_options()
    problems = check_options(opts)
    if problems:
        say("Some settings need attention before the app can start:")
        for number, problem in enumerate(problems, start=1):
            say(f"Problem {number}: {problem}")
        stop("Fix these on the Configuration tab, save, then start the app again.")

    password_file = write_secret(opts["router_password"])

    say(f"Router address is {clean_address(opts['router_address'])}.")
    if opts.get("allow_changes"):
        say("Changes are allowed. Claude will show each change and wait for your confirmation before applying it.")
    else:
        say("Read only mode. Claude can look at your network but cannot change anything.")

    # HTTP only, so the server needs nothing on standard input.
    server = subprocess.Popen(
        ["unifi-network-mcp"],
        env=server_environment(opts, password_file),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=sys.stdout,
    )

    processes = [server]

    def shutdown(signum=None, frame=None, exit_code: int = 0) -> None:
        say("Stopping.")
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        try:
            os.remove(password_file)
        except OSError:
            pass
        sys.exit(exit_code)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    if not wait_for_port(SERVER_HOST, SERVER_PORT, server, seconds=90):
        stop("The UniFi server did not start. Read the lines above for the reason, often a wrong address, username or password.")
    say("The UniFi server is running inside this app.")

    relay_configured = bool((opts.get("relay_address") or "").strip())
    if relay_configured:
        relay = subprocess.Popen(
            ["unifi-mcp-relay"],
            env=relay_environment(opts),
            stdin=subprocess.DEVNULL,
            stdout=sys.stdout,
            stderr=sys.stdout,
        )
        processes.append(relay)
        say("Connecting to your private relay. Claude can reach your network once the relay reports it is connected.")
    else:
        say("No relay is set up yet, so Claude cannot reach this app. That is fine for a first test.")
        say("When you are ready, fill in Relay address and Relay token on the Configuration tab and restart the app.")

    while True:
        for process in processes:
            code = process.poll()
            if code is not None:
                name = "UniFi server" if process is server else "relay"
                say(f"The {name} stopped unexpectedly with code {code}. Restarting the app is the usual fix.")
                shutdown(exit_code=1)
        time.sleep(5)


if __name__ == "__main__":
    main()
