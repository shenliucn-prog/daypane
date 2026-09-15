# 免费云端看板：外部定时触发 + Actions + Pages

[English](CLOUD_DEPLOY.md) | **简体中文** · [返回 README](../README.zh-CN.md)

## 结构

- `main`：源码、布局、配置模板、测试。
- `runtime-data`：独立的额度输入分支，根目录 `quotas.json`；不触发源码 CI。
- Pages 部署产物：`screen.png`、`status.json`、状态网页，不写进任何源码提交。
- 原始 Dashboard JSON 仅在运行任务中使用，不公开发布。

已有 `gh-pages` 留作迁移回退；新流程不再向它提交。

## 外部触发配置

在 cron-job.org 创建任务：

- 名称：DayPane half-hour render
- URL：`https://api.github.com/repos/shenliucn-prog/shawn-kanban/actions/workflows/render.yml/dispatches`
- 方法：POST
- 请求正文：`{"ref":"main"}`
- 每小时第 25、55 分钟运行。当前任务时区为 America/Los_Angeles，这两个分钟位置与 UTC 一致。留几分钟给生成和发布，让 Kindle 在整点/半点取图。
- 请求头 `Accept: application/vnd.github+json`
- 请求头 `Content-Type: application/json`
- 请求头 `Authorization: Bearer <专用令牌>`

专用 GitHub fine-grained token 应只选 `shawn-kanban` 仓库，授予 Actions: write 和必需的 Metadata 读取权限，用于触发工作流。设置有效期并在到期前更新。不要把现有全账户令牌交给外部定时平台。凭证只填入定时器的认证请求头，不放 URL、不写进 Git。

API 成功接受触发与图片发布成功是两件事。定时器请求很快返回，不等待生成；生成和部署结果在 GitHub Actions 检查。

GitHub 自带第 17、47 分钟定时仅为备份；`cancel-in-progress: false` 避免新触发中断正在生成的任务。外部定时也不能保证 GitHub 运行器绝对准点。

## Pages

Settings → Pages → Source 设为 GitHub Actions。工作流使用 upload-pages-artifact / deploy-pages；图源地址不变：

`https://shenliucn-prog.github.io/shawn-kanban/screen.png`

状态页：`https://shenliucn-prog.github.io/shawn-kanban/`

机器状态：`https://shenliucn-prog.github.io/shawn-kanban/status.json`

每次运行先读取上一张图片和校验和。公开数据全部失败、字体不可用或渲染失败时保留上一张好图，并发布失败状态。若安装依赖等更早步骤失败，则不产生新部署，已有 Pages 保持不动。状态网页按真实生成时间计算年龄，超过 45 分钟显示过期。

`status.json` 保留最近 256 次生成结果、生成时间、任务 ID、触发类型。精确触发/排队/部署时间另由 GitHub run / job API 记录，不能把 API 接受触发当作发布完成。

## 中英文输出

每轮采集一次数据，分别生成两种语言图片。现有 `screen.png` 与根目录预览保持中文；`screen-en.png` 为英文图，英文预览和独立状态记录位于 `en/`。生成失败时按语言保留旧图；首次生成失败且没有旧图时不发布。

仓库默认展示英文，设备语言通过插件 **Language / 语言** 单独选择。英文新闻使用 HN，中文新闻源保持原样；自定义名称不会自动翻译。

## 本机额度上报迁移

更新上报器，并将现有私有配置中的 `GITHUB_BRANCH=main` 改为 `GITHUB_BRANCH=runtime-data`。默认远端路径改为 `quotas.json`。

本地文件放在 `SHAWN_DATA_DIR`，默认 `~/.local/share/shawn-kanban/`。成功上传记录与本地采集分开，失败下轮重试；默认五分钟心跳避免用量不变时误判离线。

AI 指标含义保持原样：Claude Code 栏实际统计 WorkBuddy 消息，Codex 栏统计文件活动，不能视为账户真实额度。不要把敏感任务文本加入运行输入；runtime-data 与现有仓库同样公开。

## 48 小时验收

从外部定时器启用后开始计时：检查每次外部请求是否被接受、Actions 是否执行、Pages 是否发布，以及图片生成时间是否超过 45 分钟。源码中的备份 cron 不算外部定时器验收完成。Kindle 休眠/唤醒仍需单独实机验证。
