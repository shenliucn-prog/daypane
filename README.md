# Shawn Kanban — an always-on dashboard for jailbroken Kindle

> v0.3.3: While the dashboard is visible, hold-awake mode is enabled by default. Manual sleep pauses updates until wake; recurring RTC wake is disabled by default. Wi-Fi management and automatic radio shutdown are opt-in. Only Wi-Fi started by this plugin is shut down. Replace the plugin folder as a whole; runtime.lua is obsolete.

[简体中文](README.zh-CN.md) | **English (default)**

A Windows/macOS Node.js service and cloud renderer for an e-ink dashboard: WorkBuddy / Claude Code / Codex activity estimates, weather, US and A-share markets, world clocks, and exchange rates. The KOReader **Shawn Kanban** plugin downloads full-screen images and refreshes at :00 and :30 while the dashboard is open.

English is the default repository language. The Kindle plugin supports English and Chinese menus, messages, and rendered dashboards. New installations follow the KOReader interface language (Chinese locales use Chinese; other locales use English). Existing installations with saved server settings retain Chinese until you explicitly switch.

Select **Shawn Kanban → Language / 语言 → English / 中文** to choose independently of your Kindle firmware language. This uses the same plugin on English and Chinese Kindles; a jailbroken device and KOReader are still required.

## Install v0.3.3

Download the versioned plugin ZIP from [Releases](https://github.com/shenliucn-prog/shawn-kanban/releases). Follow [installation, upgrade and rollback](docs/UPGRADE.md); copy the whole plugin folder, not just main.lua.

Use the [configuration tool](https://shenliucn-prog.github.io/shawn-kanban/setup/) to set your own renderer's city, timezone, temperature unit, screen dimensions, font scale and modules. Import existing config.json to preserve other settings. Templates: daily, work, minimal. Downloaded settings apply to your own renderer, not the public demo.

On the Kindle, **Setup / test image** checks your source and **Device status** separates content age from download time. See [display protocol](docs/PROTOCOL.md) for custom integrations. Wi-Fi management and night schedule are opt-in; an experimental RTC test is supervised and single-shot.

## Cloud deployment

cron-job.org triggers GitHub Actions at **:25 and :55** each hour. Actions generates an image and publishes it to GitHub Pages ahead of the Kindle's next refresh. GitHub's own schedule is a fallback. Queueing and deployment can delay updates; this is not a real-time guarantee.

- `main` contains source code; `runtime-data` stores quota input in a separate branch of the same repository.
- Generated images are published as Pages deployment artifacts, not source commits. On generation failure, the pipeline attempts to retain the last good image.
- The [dashboard](https://shenliucn-prog.github.io/shawn-kanban/) reports freshness; [status.json](https://shenliucn-prog.github.io/shawn-kanban/status.json) records generation time and workflow results. The web page marks images older than 45 minutes as stale.
- Public data can update while the computer is off. Local activity estimates depend on the reporter and may retain their last values.

See [cloud deployment](docs/CLOUD_DEPLOY.md). Renew the external trigger token before expiry; never commit it.

## Run locally on Windows or macOS

Requires Node.js 20 or later.

```bash
npm install
npm start
```

Open `http://127.0.0.1:8787/` for the dashboard or `/api/dashboard` for JSON. Connect the Kindle and computer to the same network and enter the computer's LAN address in the plugin's **Set LAN server** menu. See the [Mac setup guide](MAC_SETUP.md).

Optional startup management: install PM2, run `pm2 start src/index.js --name shawn-kanban`, and configure startup persistence for your operating system. On macOS, `pm2 save` and `pm2 startup` provide the setup instructions.

## Configuration

Environment variables override `config.json`.

| Setting | config.json | Environment variable |
|---|---|---|
| Bind address / port | `host` / `port` | `HOST` / `PORT` |
| Weather location | `weather.city/lat/lon` | `DASH_CITY` / `DASH_LAT` / `DASH_LON` |
| Stocks | `stocks` | `DASH_STOCKS` (JSON) |
| World clocks | `clocks` | `DASH_CLOCKS` (JSON) |
| Activity caps | `claudeCap` / `codexCap` | `DASH_CLAUDE_CAP` / `DASH_CODEX_CAP` |
| WorkBuddy database | — | `WORKBUDDY_DB_PATH` |

Market data uses Tencent Finance, weather uses Open-Meteo, and FX uses open.er-api.com. These integrations do not require an API key. See `config.json` for the configured instruments and locations. AI activity metrics are estimates, not authoritative account quotas; the cloud reporter's current labels and limitations are explained in the deployment guide.

## Kindle installation and upgrade

Requires a jailbroken Kindle with KOReader.

1. Exit KOReader and connect the Kindle by USB.
2. Back up `koreader/plugins/KindleDash.koplugin/` before upgrading, then replace it with this repository's `KindleDash.koplugin/` folder.
3. Safely eject the device, restart KOReader, and open Tools → **Shawn Kanban** → **Refresh dashboard**.
4. Under **Set cloud image URL**, use `https://shenliucn-prog.github.io/shawn-kanban/screen-en.png` for English or `https://shenliucn-prog.github.io/shawn-kanban/screen.png` for Chinese. New installations choose the built-in URL for their language. Existing settings are preserved; an existing empty URL must be filled in manually.
5. For local service access, set **Set LAN server** to your computer's `IP:8787` and allow inbound TCP 8787. Cloud-only use requires no inbound computer port.

Image fallback order: **LAN computer → cloud → local cache**. An offline computer can cause a timeout before the plugin tries the cloud. HTTPS validates certificates and requires KOReader's CA bundle.

### Display, sleep, and refresh

- Tap the top 10% of the screen, swipe down from the top 25%, or use a Back key if available to exit.
- While the dashboard is open, the plugin pauses KOReader autosuspend and resets the Kindle native idle timer every four minutes through KOReader's power API, respecting charging and KeepAlive state. Closing the dashboard or unloading the plugin cancels the timer and restores the previous autosuspend setting.
- The power button still permits manual sleep. After resume, refresh is attempted after approximately 5 seconds. Failed attempts retry at 1, 2, 4, 8, 16 and then 30 minutes. Wi-Fi management is opt-in; see the upgrade guide.
- Scheduled refresh defaults to :00 and :30 while the dashboard is displayed and can be configured from 5 to 1440 minutes. Turning off automatic refresh cancels that timer; manual and resume refresh remain available.
- **This does not implement scheduled wake from deep sleep.** UI timers cannot refresh a suspended device. Keeping the dashboard running increases battery consumption.

The fix passes Lua syntax and simulated behavior tests. Real-device sleep, Wi-Fi recovery, and long-term battery testing remain pending.

### Device checks and rollback

Stop the local computer service and confirm cloud images still load. Leave the dashboard open for at least 35 minutes and check the image's generation time. Manually sleep and wake the Kindle, confirm refresh after network recovery, then close the dashboard and confirm normal autosuspend.

To roll back, exit KOReader, restore the backed-up plugin folder, and restart. If an image is old, inspect public `status.json`: a fresh cloud timestamp points to device connectivity or the plugin; an old cloud timestamp points to Actions or the external scheduler.

## Dashboard language and compatibility

- The existing `screen.png` and root Pages view stay Chinese for existing users. English is available at [`screen-en.png`](https://shenliucn-prog.github.io/shawn-kanban/screen-en.png) and the [English preview](https://shenliucn-prog.github.io/shawn-kanban/en/). Each locale retains its own last good image and status history (`status.json` / `en/status.json`).
- The plugin switches built-in cloud URLs when you change its language, while preserving custom URLs. For a custom image server, configure its matching language URL yourself. Image caches are separate by language.
- Local image requests use `/api/screen?lang=en` or `?lang=zh`; the local browser dashboard remains Chinese. Set `PYTHON_BIN` if Python is not on PATH; install Pillow for local rendering.
- Direct rendering supports `python tools/render_screen.py --data dashboard.json --lang en --out screen-en.png` (`zh` is the backward-compatible default).
- English rendering uses English section labels, weather descriptions, stock symbols, MLB abbreviations, HN headlines, and `data/quotes.en.txt`. Chinese sources and `data/quotes.txt` remain unchanged. Built-in city names are localized; custom labels are not machine-translated. MLB times remain UTC+8 in both versions.
- Language support does not remove the jailbreak/KOReader requirement or guarantee compatibility with every Kindle model. The default output is 1072×1448; renderer dimensions can now be configured, and the plugin scales the image; English firmware has not been tested on a physical device here.

## Development checks

```bash
npm ci
npm run lint
npm test
python -m pip install lupa Pillow
python tools/check_lua.py KindleDash.koplugin/main.lua KindleDash.koplugin/sha256.lua
python -m unittest discover -s test -p "*_test.py"
```

Lua tests use a simulated KOReader API to cover HTTPS body collection, failed requests, timer cancellation, suspend/resume retries, and cleanup. They do not replace device testing.

## Documentation languages

Keep Chinese and English document pairs in sync when changing behavior or setup instructions. English files are the default entry points; `.zh-CN.md` files are their Chinese counterparts. Code identifiers, URLs, and configuration keys stay unchanged.

## Layout configuration

Add a `display` object to config.json (or use `SHAWN_CONFIG` to select another file):

```json
{"display":{"preset":"daily","modules":["news","ai","weather","market","clocks","mlb","quote"],"width":1072,"height":1448,"fontScale":1,"timezone":"Asia/Shanghai","temperatureUnit":"C"}}
```

Modules are ordered and optional; unknown or duplicate names are rejected. Use fewer modules for landscape or larger text. If content exceeds the selected screen, rendering fails and the cloud retains the last good image. The configuration preview is a structural sketch, not live data or a guarantee of pixel fit. Renderer timezone controls header and fetch timestamps; world-clock zones and MLB UTC+8 are independently defined. Windows may need `pip install tzdata` for IANA timezone support.
