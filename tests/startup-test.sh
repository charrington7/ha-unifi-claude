#!/bin/sh
# Build the app and check it starts. Needs Docker. Run from the repository's top folder.
# Prints one plain sentence per check; the last line says whether everything passed.
set -eu

image="ha-unifi-claude-test:$$"
work="$(mktemp -d)"
cleanup() {
    docker rm -f "uc-bad-$$" "uc-good-$$" >/dev/null 2>&1 || true
    docker rmi -f "$image" >/dev/null 2>&1 || true
    rm -rf "$work"
}
trap cleanup EXIT

say() { echo "Test: $1"; }
fail() { echo "Test FAILED: $1"; exit 1; }

say "building the app."
docker build -q -t "$image" unifi_mcp >/dev/null || fail "the app did not build."

say "checking empty settings are reported in plain words."
printf '%s' '{"router_address":"","router_username":"test","router_password":"test","router_port":443,"site_name":"default","check_router_certificate":false,"allow_changes":false,"relay_address":"","relay_token":"","location_name":"Home","detailed_logs":false}' > "$work/bad.json"
chmod 644 "$work/bad.json"
set +e
out="$(docker run --name "uc-bad-$$" -v "$work/bad.json:/data/options.json:ro" "$image" 2>&1)"
code=$?
set -e
[ "$code" -eq 1 ] || fail "empty settings should stop the app with code 1, got $code."
echo "$out" | grep -q "Router address is empty" || fail "the empty router address was not reported."

say "checking the server starts and listens only inside the app."
printf '%s' '{"router_address":"192.0.2.1","router_username":"test","router_password":"test","router_port":443,"site_name":"default","check_router_certificate":false,"allow_changes":false,"relay_address":"","relay_token":"","location_name":"Home","detailed_logs":false}' > "$work/good.json"
chmod 644 "$work/good.json"
docker run -d --name "uc-good-$$" -v "$work/good.json:/data/options.json:ro" "$image" >/dev/null
started=no
i=0
while [ $i -lt 60 ]; do
    if docker logs "uc-good-$$" 2>&1 | grep -q "The UniFi server is running inside this app"; then started=yes; break; fi
    if [ "$(docker inspect -f '{{.State.Running}}' "uc-good-$$")" != "true" ]; then break; fi
    sleep 2
    i=$((i + 1))
done
if [ "$started" != yes ]; then
    docker logs "uc-good-$$" 2>&1 | tail -15
    fail "the UniFi server did not start inside the app."
fi
docker logs "uc-good-$$" 2>&1 | grep -q "No relay is set up yet" || fail "the no-relay message is missing."

say "checking the server keeps running on HTTP alone, with nothing on its input."
sleep 20
if [ "$(docker inspect -f '{{.State.Running}}' "uc-good-$$")" != "true" ]; then
    docker logs "uc-good-$$" 2>&1 | tail -15
    fail "the app stopped after it started."
fi
docker logs "uc-good-$$" 2>&1 | grep -q "UNIFI_MCP_STDIO_ENABLED=false: running" || fail "the server did not report HTTP-only mode."

say "all checks passed."
