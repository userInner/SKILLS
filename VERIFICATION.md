# Skill 核验流水线

平台每天从尚未核验的 Registry 记录中，按分类轮询选择最多 30 个 Skill。每个分类优先处理仓库内已整理的 `direct` 包，再按来源 Star 和名称处理第三方 `extracted` 包。

核验只读取文件，不执行来源脚本，也不安装来源依赖。记录以下可复现结果：

- 来源是否固定到完整 Git Commit；
- 本地目录 SHA-256 是否与 Registry 一致；
- `SKILL.md`、frontmatter、文件边界和符号链接是否合规；
- 基础静态扫描是否仍为通过；
- 复制到临时隔离目录后，摘要和 `SKILL.md` 是否仍可复验；
- 文件数、总字节数、来源命令执行数和网络请求数。

每次结果写入 `verifications/v1/<release-id>.json`。记录只新增、不覆盖；Skill 内容或来源 Commit 变化后会生成新的 Release ID 和新的核验记录，旧记录保留为历史证据。

GitHub Actions 只允许自动合并新增核验证据及其确定性 Registry 投影。能力身份、来源、内容摘要或既有证据发生变化时，安全门会停止自动合并并要求人工审核。

本地演练：

```bash
python3 scripts/verify_registry_skills.py --limit 30 --dry-run
python3 scripts/build_registry_v1.py --check
```
