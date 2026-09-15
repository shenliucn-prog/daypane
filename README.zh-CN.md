# DayPane（日窗）— Kindle 墨水屏改造看板

把闲置 Amazon Kindle 改造成常驻墨水屏信息看板：天气、世界时钟、行情和每日资讯。DayPane 是开源的 Kindle 改造／旧设备再利用项目，由 KOReader 插件、本地 Node.js 服务和 GitHub Actions 云端生成器组成。需要先完成越狱并安装 KOReader；本项目不提供越狱工具。

原名 **Shawn Kanban / Kindle Dash**。仓库及 GitHub Pages 路径暂时保留 `shawn-kanban`，让已有 Kindle 图源地址和定时任务继续可用。插件目录仍为 `KindleDash.koplugin`，保留已有配置及中英文偏好。当前 v0.3.3 安装包仍显示旧名称，源码已使用 DayPane。

> v0.3.3：看板显示期间默认保持唤醒；手动休眠后暂停更新，唤醒后恢复。周期 RTC 唤醒默认关闭。联网管理和自动关闭 Wi-Fi 均需主动开启，且仅关闭插件自己开启的无线电。升级请整体替换插件目录，runtime.lua 已不再使用。

[English](README.md) | **简体中文**

跨平台（Windows / macOS）Node.js 服务，把越狱 Kindle 的墨水屏变成一张常驻看板：
**WorkBuddy / Claude Code / Codex 限额、天气、美股 + A股（带 30 日走势图）、世界时钟、汇率**，
由电脑或云端生成整屏图片，KOReader 的 **DayPane** 插件负责下载和显示。看板打开时，每个整点/半点自动刷新（如 08:30、09:00）。

仓库默认展示英文，本文为中文说明。Kindle 插件支持中英文菜单、提示和图片；新安装按 KOReader 语言选择，已有服务器配置的用户升级后保留中文。通过 **DayPane → Language / 语言 → English / 中文** 可独立选择，不要求更改 Kindle 固件语言。Mac 局域网配置见 [Mac 安装指南](MAC_SETUP.zh-CN.md)。

## 安装 v0.3.3

从 [Releases](https://github.com/shenliucn-prog/shawn-kanban/releases) 下载版本安装包，按 [升级与回退说明](docs/UPGRADE.zh-CN.md) 复制完整插件目录（main.lua 和 sha256.lua）。你的中文地址与配置保留。

使用 [配置工具](https://shenliucn-prog.github.io/shawn-kanban/setup/) 设置自己生成端的城市、时区、温度单位、屏幕尺寸、字号及模块顺序。可先导入旧 config.json 保留其他设置；提供日常、工作、极简模板。下载的配置需要放到自己的生成端，不会改变公共示例。

Kindle 菜单新增设置／测试图片、设备状态、刷新间隔、按需联网和夜间降频。RTC 是需确认的单次实验，不默认开启。设备状态将图片生成时间与下载时间分开，避免旧图伪装为新数据。

## 免费云端部署

采用 cron-job.org 外部定时触发 + GitHub Actions 生成 + GitHub Pages 发布：每小时第 **25、55 分钟**触发，供 Kindle 在整点、半点取图。GitHub 自带定时任务作为备用；触发和发布可能延迟，不保证准点。

- 源码在 `main`，额度输入在独立 `runtime-data` 分支；仍属于同一仓库。
- 新生成图片通过 Pages 部署产物发布，不提交到源码分支。生成失败时尽量保留上次成功图片。
- [网页版看板](https://shenliucn-prog.github.io/shawn-kanban/)显示更新状态；[status.json](https://shenliucn-prog.github.io/shawn-kanban/status.json)记录生成时间和工作流结果。超过45分钟未更新时，网页标记过期。
- 电脑关闭时仍可生成公共数据；本机额度数据取决于上报程序，可能保持最后一次的值。

配置与状态检查见 [云端部署](docs/CLOUD_DEPLOY.zh-CN.md)。外部触发所用令牌到期前需更新；不要把令牌写入仓库。

## 运行（Windows 或 macOS 通用）

```bash
npm install
npm start
# 浏览器打开 http://127.0.0.1:8787/       看网页版看板（单页、30s 整点半点自动刷新、SVG 折线图）
#           http://127.0.0.1:8787/api/dashboard  拿 JSON
```

在 **MacBook** 上工作时，同样地 `npm install && npm start`，让 Kindle 连同一个 WiFi，
把插件（工具 → DayPane）里的服务器地址改成 MacBook 的局域网 IP（菜单 → 设置服务器地址）。

### 让服务开机自启 / 崩溃自拉起（可选）
- Windows：`npm install -g pm2` 后 `pm2 start src/index.js --name shawn-kanban`
- macOS：`brew install pm2 && pm2 start src/index.js --name shawn-kanban`，再 `pm2 save && pm2 startup`

## 配置（config.json 或环境变量，环境变量优先）

| 项目 | config.json | 环境变量 |
|------|-------------|----------|
| 绑定地址/端口 | `host` / `port` | `HOST` / `PORT` |
| 城市与坐标 | `weather.city/lat/lon` | `DASH_CITY` / `DASH_LAT` / `DASH_LON` |
| 股票列表 | `stocks` | `DASH_STOCKS`(JSON) |
| 世界时钟 | `clocks` | `DASH_CLOCKS`(JSON) |
| 限额上限 | `claudeCap` / `codexCap` | `DASH_CLAUDE_CAP` / `DASH_CODEX_CAP` |
| WorkBuddy 库路径 | — | `WORKBUDDY_DB_PATH` |

股票默认：苹果(AAPL)、美光(MU)、贵州茅台、长鑫科技(688825)，每只带 30 日收盘走势。
数据源：天气=Open-Meteo、汇率=open.er-api.com、股票=腾讯财经（gtimg），**均免 API key**。
限额中的 Claude Code / Codex 取自本机历史目录近 7 天的统计，为近似值（标注 `本地`）。

## Kindle 安装与升级

需要已越狱的 Kindle 和 KOReader。

1. 退出 KOReader，通过 USB 连接电脑。
2. 升级前备份设备中的 `koreader/plugins/KindleDash.koplugin/`，再用本仓库同名文件夹覆盖。
3. 安全弹出设备，重启 KOReader → 工具 → **DayPane** → **刷新看板**。
4. 在 **设置云端图地址** 中确认完整图片地址：`https://shenliucn-prog.github.io/shawn-kanban/screen.png`。新安装默认使用此地址；升级保留原配置，原先留空的地址需手动填写。
5. 如使用局域网服务，在 **设置局域网服务器** 中填写电脑的 `IP:8787`，电脑防火墙需放行 TCP 8787。仅用云端无需开放电脑端口。

取图顺序为 **局域网电脑 → 云端 → 本地缓存**。电脑不在线时会先等待局域网请求超时，再尝试云端。云端 HTTPS 下载校验证书，需要 KOReader 自带的有效 CA 证书文件。

### 显示、休眠与刷新

- 点击屏幕顶部10%区域，或从顶部25%区域向下滑动，可退出看板；有返回键的设备也可按返回键退出。
- 看板打开时暂停 KOReader 自动休眠，并每4分钟通过 KOReader 的 Kindle 电源接口重置系统空闲计时；兼容已有 KeepAlive 状态及充电状态。退出看板或卸载插件时取消计时并恢复原休眠设置。
- 电源键仍可手动休眠。唤醒后约5秒尝试刷新；失败按1、2、4、8、16、30分钟退避重试。按需联网可选择开启，默认不改变网络状态。
- 自动刷新默认在整点、半点执行，可配置5–1440分钟，仅看板显示期间取图；关闭自动刷新会取消该定时器，手动刷新和唤醒刷新仍可用。
- **当前不是深度休眠后的定时唤醒方案**：设备真正休眠时不能依靠界面定时器刷新。常驻看板通过保持运行实现刷新，会增加耗电。

本次修复已通过 Lua 语法和模拟行为测试；尚未完成真机睡眠、Wi-Fi 恢复和长期耗电验证。

### 真机检查与回退

关闭电脑上的本地服务后，确认 Kindle 仍能获取云端图片；看板保持打开至少35分钟，核对图中生成时间是否变化。再按电源键休眠、唤醒，确认恢复联网后刷新；退出看板后确认能正常自动休眠。

遇到问题可退出 KOReader，恢复备份的插件文件夹并重启。若显示旧图，先检查公开 `status.json`：云端生成时间已更新而 Kindle 没变，优先检查设备联网和插件；云端也未更新，则检查 Actions 和外部定时任务。

## 中英文图片

你的现有 `screen.png` 和根目录预览继续保持中文。英文用户使用 `screen-en.png` 或 `/en/` 预览；英文状态记录在 `en/status.json`。两种语言独立保留上一张好图和缓存。

切换插件语言时自动切换内置云端图地址，自定义地址保持原值，需自行填写对应语言图源。局域网支持 `/api/screen?lang=en` 或 `?lang=zh`；本地浏览器看板仍为中文。直接渲染可使用 `--lang en`，未指定时保持中文。局域网渲染需要 Python 和 Pillow，可通过 `PYTHON_BIN` 指定 Python 路径。

英文图使用英文栏目、天气描述、股票代码、MLB 缩写、HN 英文新闻和 `data/quotes.en.txt`。内置城市名有英文对应，自定义名称不会自动翻译；两种语言的 MLB 时间均为 UTC+8。中文新闻与 `data/quotes.txt` 保持原样。

语言支持仍要求越狱与 KOReader，不代表所有 Kindle 机型均已验证。输出为1072×1448，由插件适配屏幕；尚未进行英文固件真机测试。

## 开发验证

```bash
npm ci
npm run lint
npm test
python -m pip install lupa Pillow
python tools/check_lua.py KindleDash.koplugin/main.lua KindleDash.koplugin/sha256.lua
python -m unittest discover -s test -p "*_test.py"
```

Lua 行为测试使用模拟的 KOReader 接口，覆盖 HTTPS 图片收集、网络失败、定时器取消、休眠与唤醒重试及清理，不替代真机验证。

## 文档语言约定

修改功能或部署步骤时，同步更新中英文文档。英文文件为默认入口，`.zh-CN.md` 为对应中文版；代码标识符、URL 和配置键名保持一致。

## 布局配置

通过配置工具，或在 config.json 中添加 `display`：

```json
{"display":{"preset":"daily","modules":["news","ai","weather","market","clocks","mlb","quote"],"width":1072,"height":1448,"fontScale":1,"timezone":"Asia/Shanghai","temperatureUnit":"C"}}
```

模块列表决定开关与顺序，拒绝未知和重复模块。横屏或大字号请减少模块；内容超过屏幕时生成失败并保留云端旧图。预览仅为结构示意。生成端时区控制页眉与采集时间，世界时钟和 MLB UTC+8 单独定义。可用 `SHAWN_CONFIG` 指定配置文件；Windows 时区支持可能需要 `pip install tzdata`。
