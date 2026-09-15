# Connect the Kindle dashboard to a Mac

[简体中文](MAC_SETUP.zh-CN.md) | **English (default)** · [README](README.md)

Use this guide when your Mac provides data over the LAN. For cloud-only images, follow the [Kindle installation guide](README.md#kindle-installation-and-upgrade); no local Mac service is needed.

## Start the local service

Install Node.js 20 or later, then run in the project directory:

```bash
npm install
npm start
```

Open `http://127.0.0.1:8787/` to check the service. If native dependency compilation fails, install Xcode Command Line Tools and retry:

```bash
xcode-select --install
```

See [configuration](README.md#configuration) for cities, stocks, and ports.

## Connect the Kindle

1. Connect the Mac and Kindle to the same network with device-to-device access.
2. Find the Mac's current LAN IP in macOS network settings.
3. In KOReader → Tools → DayPane → **Set LAN server**, enter `IP:8787`, such as `192.168.1.23:8787`.
4. Select **Refresh dashboard**. See the [README](README.md#kindle-installation-and-upgrade) for plugin installation, cloud configuration, and sleep behavior.

## Troubleshooting

- First verify the dashboard opens on the Mac, then check the IP and port.
- If the macOS firewall is enabled, allow inbound connections for the Node executable running the service. There is no need to disable the entire firewall.
- Guest networks and client isolation may block device-to-device connections. Use a home network that allows them, or use the cloud image source.
- When the Mac sleeps or its service stops, the plugin tries the cloud and then the device cache.

## Data and device checks

Missing local history or databases may make the corresponding activity data unavailable. AI metrics are estimates; see [reporter limitations](docs/CLOUD_DEPLOY.md#local-reporter-migration).

Back up the plugin before upgrading. Verify both LAN and cloud downloads, :00/:30 refresh, recovery after power-button sleep, and normal power saving after closing the dashboard. Consult your jailbreak's instructions for firmware compatibility; this project does not manage firmware updates.
