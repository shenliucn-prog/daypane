# Changelog

## 0.3.2

- Field test verdict on the Paperwhite 3: the RTC alarm does fire (crash.log shows the scheduled
  wake and a hardware resume), but the device wakes ~90–100 s after the programmed epoch, which
  exceeds `WakeupMgr:wakeupAction(90)`'s proximity window. The queued task is therefore rejected
  ("Kindle unscheduled wakeup") and never runs. Recurring RTC wake cannot deliver auto-refresh on
  this device and is now opt-in (`rtc_wake` setting, default off).
- Hold-awake mode replaces it (on by default): while the dashboard is shown, the plugin pauses
  KOReader's AutoSuspend (`PluginShare.pause_auto_suspend`) and blocks the firmware
  screensaver/suspend (`lipc-set-prop com.lab126.powerd preventScreenSaver 1`) — the same
  dual-channel approach the device's keepalive plugin uses. The UI timer then refreshes on
  schedule; a menu toggle turns the mode off.
- Manual power-key suspend still works: suspending releases the hold, and resuming re-engages it
  when the dashboard is still on screen. Closing the dashboard releases the hold so the device
  sleeps normally again.
- Suspend health records now say `hold-screen mode` / `rtc armed` / `rtc NOT armed`, and hold
  engagement is recorded (`hold_screen_on`/`hold_screen_off`), so the refresh mode is always
  visible in the log. Device status shows the hold state.

## 0.3.0

- Merged the `runtime.lua` overlay into `main.lua`. The old dual-layer plugin was loaded as
  `main.lua` + `dofile('runtime.lua')`, so `runtime.lua` silently redefined `fetchScreen`,
  `armAutoRefresh`, `onResume`, `holdAwake` and `init`; roughly half of `main.lua` was dead code
  and edits there had no effect. The plugin is now a single implementation.
- Fixed: waking the device with the power key could leave the dashboard unclosable until reboot.
  `onResume` used to call `power.resetT1Timeout()` (Kindle `powerd` native) synchronously at the
  suspend/resume boundary, which deadlocked the UI event loop.
- Fixed: the dashboard never auto-refreshed while idle. `holdAwake` relied on
  `PluginShare.pause_auto_suspend` + `resetT1Timeout`, which do not stop firmware screen savers on
  Kindle; the device suspended anyway and `UIManager:scheduleIn` timers stop while suspended.
  Those hacks are gone.
- Auto-refresh now uses RTC wake: the device sleeps normally and `Device.wakeup_mgr:addTask()`
  wakes it once per interval to refresh and re-arm the next wake. No always-on, no screen saver fight.
- HTTPS CA bundle is now resolved at `<datadir>/data/ca-bundle.crt` with a fallback, instead of the
  wrong `<datadir>/ca-bundle.crt`. The previous path made every cloud fetch fail with
  "CA bundle missing".
- `requestRefresh` always releases its re-entrancy lock, so a skipped background refresh can no
  longer stop auto-refresh permanently.
- Restored managed Wi-Fi (`managed_wifi` / `wifi_off`) before each fetch with a 60-second deadline,
  since a Kindle that wakes from RTC wake usually has Wi-Fi off.

## 0.3.1

- Cache writes use a unique temporary file. Two concurrent refreshes (UI timer, RTC wake, resume) used to share one `.pending` file, so the slower one kept appending into the file the faster one had already renamed — a corrupt image that then persisted on screen.
- Suspending during a refresh no longer wedges the re-entrancy lock. `_busy` stayed `true` and every later refresh returned immediately, so auto-refresh died until a restart.
- A manual refresh can now preempt an in-flight background refresh instead of being dropped with no feedback.
- Resume refresh goes through the shared refresh entry point, so it also gets managed Wi-Fi and the backoff retry instead of a second, competing retry loop.
- Suspend records whether the RTC alarm is actually armed (`rtc armed` / `rtc NOT armed` in the health log), so a broken wake chain is visible instead of silent.
- `Device.wakeup_mgr` missing is logged and recorded instead of silently downgrading to "only refreshes while awake".
- Closing the plugin no longer clears the auto-refresh preference.
- Saving a LAN address without a port keeps the configured port instead of silently using port 80.
- Refresh interval is clamped in one place; the UI timer and the RTC wake no longer disagree.

## 0.2.0

- Versioned display manifests and SHA-256 verification, bounded downloads and decode-before-replace caches.
- Local device diagnostics, battery event history and bounded retry backoff.
- Opt-in Wi-Fi management, adjustable refresh intervals and night schedule.
- Supervised, single RTC wake experiment (not recurring and not hardware-validated).
- English/Chinese setup guidance, versioned plugin packages and rollback instructions.
- Browser-only renderer configuration, daily/work/minimal profiles, module ordering, screen dimensions, font scale, timezone and temperature units.
- Existing Chinese settings and image URLs preserved; new installs have no personal LAN default.

Physical Kindle validation and 48-hour battery measurements remain pending.
