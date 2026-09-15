@echo off
rem 复制本文件为 report_secrets.bat 并填入真实值（report_secrets.bat 已被 gitignore）
rem Token 需要仓库写权限：GitHub Settings > Developer settings > Tokens (classic) > repo
set "GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
set "GITHUB_REPO=你的用户名/daypane"
set "GITHUB_BRANCH=runtime-data"

rem 上报间隔（毫秒），默认 5 分钟
set "REPORT_EVERY=300000"

rem 设为 1 = 只写本地文件，不推远端（调试用）
rem set "REPORT_DRY=1"
