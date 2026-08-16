# 主分支保护基线

自动发现任务只更新 `automation/skill-registry`，并创建或刷新一个候选 PR。排行榜、具体 Skill 与 `registry/v1` 不再由自动任务直接写入主分支。

## GitHub 仓库设置

在默认分支的 Ruleset 中启用：

1. 必须通过 Pull Request 合并，禁止直接 push。
2. 必须通过状态检查 `validate`（工作流 `Validate concrete Skills`）。
3. 合并前分支必须与默认分支保持最新。
4. 禁止 force push 和删除默认分支。
5. GitHub Actions 默认权限设为只读；仅 `Refresh Skill registry` 任务按 job 获取 `contents: write` 与 `pull-requests: write`。

如果仓库需要多人维护，再增加至少 1 个批准和 Code Owner 审核。个人仓库可以暂不要求批准，但仍应保留 PR 与必需检查。

## 信任边界

- `pull_request` 只运行只读校验，不使用仓库密钥。
- 定时/手动更新从默认分支加载可信脚本，使用 GitHub 自动签发的短期 token。
- 第三方仓库只被克隆、解析和静态扫描；自动工作流不执行其中的脚本、安装命令或依赖。
- `extracted` 与 `needs-review` 都不是安全认证。安装和发布前仍需平台沙箱验证。
