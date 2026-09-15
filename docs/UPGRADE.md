# Installation, upgrade and rollback

> v0.3.3: While the dashboard is visible, hold-awake mode is enabled by default. Manual sleep pauses updates until wake; recurring RTC wake is disabled by default. Wi-Fi management and automatic radio shutdown are opt-in. Only Wi-Fi started by this plugin is shut down. Replace the plugin folder as a whole; runtime.lua is obsolete.

[简体中文](UPGRADE.zh-CN.md)

## Install v0.3.3

1. Download `ShawnKanban-0.3.3.zip` and `SHA256SUMS` from Releases. Verify the checksum if desired.
2. Exit KOReader and connect the Kindle over USB. Back up `koreader/plugins/KindleDash.koplugin/` **and** `koreader/settings/kindledash.lua` on your computer.
3. Copy the complete `KindleDash.koplugin` folder from the ZIP into `koreader/plugins`. Both main.lua and sha256.lua are required; do not copy only main.lua.
4. Safely eject, restart KOReader, open Tools → DayPane → Setup / test image.
5. Choose Language / 语言, and confirm the device status screen reports the expected dimensions and a fresh image.

The public built-in URLs are demos using Shawn's configuration. New installs no longer attempt Shawn's LAN IP. To customize city, timezone, units or layout, use `/setup/` on the Pages site (or open `web/setup/index.html` locally), download config.json and place it on **your own renderer**. You can import existing config first; unknown settings are preserved. The form does not upload data or change the hosted demo.

Existing host, URL and language settings are preserved. Existing Chinese users remain Chinese. Automatic-refresh preference is now persisted. A custom PNG URL still works without metadata; its generation time is reported as unknown. For checksums and content age, use a protocol-v1 manifest URL.

## Normal and power-saving use

Default behavior does not force Wi-Fi on or off. Enable “Connect Wi-Fi for updates” to let KOReader reconnect for the dashboard. “Turn off Wi-Fi started by dashboard” only turns off a radio that was off before the dashboard's request. Existing Wi-Fi connections are not shut down. Network timeouts and failed requests retry at 1, 2, 4, 8, 16 and then 30 minutes. Successful requests reset the backoff.

Night schedule reduces automatic refresh to at least two hours between 23:00 and 07:00 in the **device's timezone**. The renderer's timezone is separate. Refresh interval is adjustable from 5 to 1440 minutes; a faster polling rate does not make the public half-hour source generate faster.

The dashboard still keeps the device running between updates. This is not a validated deep-sleep product. The experimental menu provides **one** confirmed two-minute RTC alarm test using KOReader's wakeup manager when available. It is off by default, does not repeat, and must be supervised on a real device. Use the power button if it does not wake. A recorded alarm callback is evidence of the callback only, not proof of a completed screen refresh. No battery-life claim is made.

## Diagnostics and validation

Device status separates content generation from download and attempt times, with image source, last error and next attempt. `settings/kindledash-health.json` retains up to 192 local events including battery percentage when available. No telemetry is uploaded.

Test a normal refresh, airplane mode, broken image URL, power-button suspend/resume and dashboard exit. Confirm an old image survives failures. For a power experiment, record battery and update success over 48 hours. Cloud monitoring cannot verify the physical screen.

## Rollback

Exit KOReader, replace the whole plugin folder with your saved backup, optionally restore the backed-up settings file, and restart. Do not delete settings or cached images just to upgrade. Releases are installable snapshots; main is the development branch. Renderer settings and generated images are not bundled in the plugin ZIP.
