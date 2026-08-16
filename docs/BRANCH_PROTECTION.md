# 主分支保护基线

自动发现任务只更新 `automation/skill-registry`，并创建或刷新一个候选 PR。排行榜、具体 Skill 与 `registry/v1` 不再由自动任务直接写入主分支。只有通过观察数据安全门的候选才会在独立校验成功后自动合并。

## GitHub 仓库设置

在默认分支的 Ruleset 中启用：

1. 必须通过 Pull Request 合并，禁止直接 push。
2. 必须通过状态检查 `validate`（工作流 `Validate concrete Skills`）。
3. 合并前分支必须与默认分支保持最新。
4. 禁止 force push 和删除默认分支。
5. GitHub Actions 默认权限设为只读；仅 `Refresh Skill registry` 任务按 job 获取 `actions: write`、`contents: write`、`pull-requests: write` 与 `statuses: write`。`actions: write` 仅用于在候选提交上触发必需的只读校验，`statuses: write` 仅用于把该次校验结果绑定回同一个候选提交。

如果仓库需要多人维护，再增加至少 1 个批准和 Code Owner 审核。个人仓库可以暂不要求批准，但仍应保留 PR 与必需检查。

## 自动合并边界

以下变化可自动合并：

- Star、排名、描述、许可证观察值与默认分支等来源元数据刷新。
- 新来源以 `index-only` 状态进入索引。
- 有明确审计证据的归档仓库或低于 300 Star 的来源移除。
- 重复来源清理。

以下任一变化都会停止自动合并并保留 PR：

- `skills/`、`community-skills/`、脚本、工作流或 Schema 变化。
- 直装数量、能力状态、验证状态或具体 Skill 内容摘要变化。
- 新来源直接成为可安装能力。
- 删除来源缺少 `archived` 或 `below-star-threshold` 审计原因。
- Registry 的能力身份、发布版本、制品或内容摘要变化。

安全候选由可信刷新任务显式触发 `Validate concrete Skills`，成功后仍通过受保护分支的正常合并接口进入主分支，不绕过 Ruleset。

## 信任边界

- `pull_request` 只运行只读校验，不使用仓库密钥。
- 定时/手动更新从默认分支加载可信脚本，使用 GitHub 自动签发的短期 token。
- 第三方仓库只被克隆、解析和静态扫描；自动工作流不执行其中的脚本、安装命令或依赖。
- `extracted` 与 `needs-review` 都不是安全认证。安装和发布前仍需平台沙箱验证。
