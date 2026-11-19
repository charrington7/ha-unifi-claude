# UniFi Network for Claude

This app runs on your Home Assistant Green, or any 64-bit Home Assistant OS machine. It lets Claude look at your UniFi network and, only if you allow it, make changes. Every change is shown to you first and waits for your confirmation.

This guide is written for screen readers. Each part is a heading level 2, so you can jump between parts with your screen reader's heading key. Steps are numbered lists. There are no images.

## How it works, in one paragraph

The app talks to your UniFi gateway over your home network. It does not open any ports on your network or on the internet. Instead, it reaches out to a small private relay that you run on your own free Cloudflare account. Claude connects to that relay with a secret token. Without the token, nobody can reach the app.

## What you need

1. Home Assistant OS, updated to a recent version, on a 64-bit machine such as the Home Assistant Green.
2. A computer for the one-time relay setup. The steps below use Windows; on a Mac or Linux the commands are the same in a terminal.
3. A free Cloudflare account. You can create one during Part 5.
4. About 45 minutes the first time.

Note on names: Home Assistant now calls add-ons "apps". If your version still says "Add-ons", the steps are the same with that word instead.

## Part 1: Make a UniFi account just for Claude

Using a separate account means you can remove Claude's access at any time without changing your own password.

1. In a web browser, go to your UniFi console's local address, for example https://192.168.1.1, and sign in.
2. Open the Admins and Users section. It is usually under Settings or in the main navigation.
3. Choose to add or create a new admin.
4. Choose the option to restrict the account to local access only. This is important: the app cannot use a Ubiquiti cloud account.
5. Give it a username such as claude, and a strong password. Do not turn on two-factor sign-in for this account; the app cannot use it.
6. For the role: choose a view-only role if you only want Claude to look. Choose a full administrator role if you want Claude to be able to make changes later.
7. Save. Write down the username and password; you will type them in Part 4.

Tip: the UniFi console's interface can be inconsistent with screen readers. If a step is hard to find, ask Claude to walk you through it using what your screen reader announces.

## Part 2: Add this app's repository to Home Assistant

1. In Home Assistant, go to Settings, then Apps, then open the app store.
2. Open the More options menu, near the top right, and choose Repositories.
3. In the Add field, paste https://github.com/charrington7/ha-unifi-claude
4. Activate Add, then Close.

## Part 3: How updates work

1. When a new version of the app is published to the repository, Home Assistant shows an update for UniFi Network for Claude under Settings, then Updates. The update dialog lists what changed, in plain words.
2. Nothing changes until you choose Update. Your settings are kept, so the relay and the Claude connector keep working.
3. Updating rebuilds the app on your machine. The progress bar can stay at 0 percent for a few minutes while it builds; that is normal.
4. To check straight away instead of waiting, open the app store's More options menu and choose Check for updates.

## Part 4: Install and test the app

1. In Home Assistant, go to Settings, then Apps, then open the app store.
2. Find the section for the UniFi Network for Claude repository, and choose UniFi Network for Claude. If it is not listed, open the More options menu and choose Check for updates, then refresh the page.
3. Activate Install. This builds the app on your machine and takes several minutes. Stay on the page until the Install button changes to Start.
4. Go to the Configuration tab and fill in:
   1. Router address: your gateway's IP address, for example 192.168.1.1.
   2. Router username and Router password: the account from Part 1.
   3. Leave Router port at 443, Site name at default, and Check router certificate off.
   4. Allow Claude to make changes: leave off for now. You can turn it on later.
   5. Leave Relay address and Relay token empty for now.
5. Activate Save.
6. Go to the Info tab and activate Start. Also turn on Start on boot, so the app returns after a power cut.
7. Go to the Log tab. Every line from this app starts with "UniFi for Claude", followed by a full sentence. You should hear "The UniFi server is running inside this app" and then "No relay is set up yet". That means Part 4 worked.

If the log lists problems instead, each one says exactly which setting to fix.

## Part 5: Set up your private relay (one time)

The relay is a tiny program that runs on your own Cloudflare account. It is the only way in, and it requires a secret token.

1. Open Windows Terminal or PowerShell.
2. Install Node.js by typing this and pressing Enter. Accept any prompts.

   winget install OpenJS.NodeJS.LTS

3. Close and reopen Windows Terminal so it finds Node.js.
4. Install the relay tools. Type each line and press Enter after each:

   npm install -g wrangler

   npm install -g unifi-mcp-worker

5. Start the relay setup:

   unifi-mcp-worker install

6. If asked to log in to Cloudflare, a browser window opens. Sign in or create a free account, then choose Allow. Return to Windows Terminal.
7. The setup asks four questions. Press Enter to accept the default for the first two: Worker name, and Base domain. For Location name, type Home and press Enter. For observability, press Enter to accept No.
   If this is a brand-new Cloudflare account, you may also be asked to choose a workers.dev subdomain. Type any short name, such as your last name, and press Enter. It becomes part of your relay's web address.
8. When it finishes, it prints three tokens and a worker web address. You do not need to read them from the terminal. They are saved in a text file you can open with Notepad: press Windows key plus R, then type

   notepad %USERPROFILE%\.unifi-mcp-worker\config.json

   and press Enter.
9. In that file, find these three values:
   1. worker_url: your relay's web address. It starts with https and ends with workers.dev.
   2. relay_token, inside the locations section: this goes into the Home Assistant app.
   3. agent_token: this goes into Claude. Treat it like a password; anyone with it and the address can reach your network through Claude's tools.

Keep the ADMIN token private as well. You will not need it for normal use.

Note for Windows: older versions of unifi-mcp-worker could not find npm or Wrangler on Windows. That was fixed upstream in https://github.com/sirkirby/unifi-mcp/issues/1048, so make sure you install the newest version.

## Part 6: Connect the app to the relay

1. In Home Assistant, open the UniFi Network for Claude app and go to the Configuration tab.
2. Relay address: paste the worker_url value.
3. Relay token: paste the relay_token value. Not the agent token.
4. Location name: Home.
5. Activate Save, then go to the Info tab and activate Restart.
6. On the Log tab you should hear "Connecting to your private relay", followed by lines from the relay saying it connected and registered tools.

## Part 7: Add the connector to Claude

1. In Claude, go to Settings, then Connectors.
2. Choose to add a custom connector.
3. Name: UniFi.
4. Remote server address: the worker_url followed by /mcp. For example https://unifi-mcp-relay.yourname.workers.dev/mcp
5. Authentication: choose No sign in.
6. Under Request headers, add one header:
   1. Header name: Authorization
   2. Value: the word Bearer, one space, then the agent_token value.
7. Save. Then start a new chat and ask: "List the devices on my UniFi network."

## Allowing changes later

When you are ready for Claude to help build your separate networks and firewall rules:

1. In the app's Configuration tab, turn on Allow Claude to make changes, then Save and Restart.
2. Make sure the UniFi account from Part 1 has a full administrator role.

Even with this on, Claude must show you each change and get your confirmation before it is applied. Turning the setting off again returns the app to look-only, no matter what is asked.

## Removing access

Any one of these cuts Claude off completely:

1. Stop the app in Home Assistant.
2. Delete or disable the UniFi account from Part 1.
3. Remove the connector in Claude's settings.
4. To get a new agent token, run this in Windows Terminal, then update the header in Claude:

   unifi-mcp-worker rotate-tokens

## Troubleshooting

1. The app is not listed after Part 2: check the repository address was pasted whole. Then run Check for updates again and refresh the page.
2. The log says the UniFi server did not start: check the router address, username and password. Make sure the account is a local account without two-factor sign-in.
3. Claude says it cannot connect: check the app's log shows the relay connected. Check the connector address ends in /mcp, and that the header value starts with the word Bearer and a space.
4. Turn on Detailed logs in the Configuration tab only while troubleshooting, then turn it off again.

## Credits

This app packages the open-source UniFi Network MCP server and relay by sirkirby, MIT license: https://github.com/sirkirby/unifi-mcp
