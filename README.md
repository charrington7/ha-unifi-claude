# ha-unifi-claude

A Home Assistant app that gives Claude safe access to a UniFi network: look-only by default, every change confirmed by you first, and no open ports. It runs on a Home Assistant Green or any 64-bit Home Assistant OS machine.

The app packages the open-source UniFi Network MCP server and relay by sirkirby (https://github.com/sirkirby/unifi-mcp) and adds a Home Assistant wrapper around them:

- Settings on the app's Configuration tab instead of environment variables.
- The MCP server listens only inside the app, on 127.0.0.1. The only way in is your own private Cloudflare relay, which the app connects out to.
- Every log line is a plain sentence, so the log reads well with a screen reader.
- A startup test (tests/startup-test.sh) that builds the app with Docker and checks it starts.

The full screen-reader-friendly setup guide is in unifi_mcp/DOCS.md. Home Assistant also shows it on the app's Documentation tab.

## Installing

1. In Home Assistant, go to Settings, then Apps, then open the app store.
2. Open the More options menu and choose Repositories.
3. Add https://github.com/charrington7/ha-unifi-claude, then Close.
4. Install UniFi Network for Claude and follow the guide.

## Status

This is a personal project, shared as a reference for the upstream discussion at https://github.com/sirkirby/unifi-mcp/issues/1047. It is not an official part of unifi-mcp.

## Credits

UniFi Network MCP server and relay by sirkirby, MIT license: https://github.com/sirkirby/unifi-mcp. App wrapper and guide by Christopher Harrington.
