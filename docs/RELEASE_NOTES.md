# Shawn Kanban v0.3.3

Fixes duplicate refresh timers, preserves cached images on filesystem failures, and limits Wi-Fi shutdown to connections owned by the dashboard. Wi-Fi management is opt-in.

Includes the v0.3.x unified plugin, corrected certificate lookup, local renderer discovery and configured Shanghai timezone. Dashboard hold-awake is enabled by default; manual sleep pauses updates until resume. Recurring RTC wake remains disabled by default.

Replace the whole KindleDash.koplugin folder after backing up settings. runtime.lua is obsolete. See the English and Chinese upgrade guides. Automated tests do not establish battery life or cross-device wake reliability; this remains a prerelease.
