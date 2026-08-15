# Community Skills

从许可证明确且已进入精选来源名单的 GitHub 仓库中，按真实 Skill 包根目录提取的候选能力包。

当前记录 **725 个具体 Skill**：

- **40 个 `direct`**：已在 `skills/` 中完成人工整理，可直装。
- **647 个 `extracted`**：包文件完整，基础静态扫描未命中；尚未完成人工验收与沙箱运行。
- **38 个 `needs-review`**：命中高风险命令模式，必须人工审查。
- **6 个 rejected**：重复、超限或结构不完整，不进入包目录。

机器读取入口：[index.json](index.json)。每个候选包包含原始 `SKILL.md`、包内依赖文件、许可证、`NOTICE.effecta` 和 `effecta.manifest.json`。

## 分类

| 分类 | Skill 数 |
|---|---:|
| `design` | 76 |
| `engineering` | 187 |
| `growth` | 44 |
| `product` | 64 |
| `research` | 40 |
| `workflow` | 294 |
| `writing` | 20 |

## 状态边界

`extracted` 只表示文件结构、体积、许可证和基础静态规则通过，不表示安全认证或运行验证。Agent 可以搜索、读取和提出安装方案；人类批准后，仍应在隔离目录校验摘要并执行该包声明的最小冒烟测试。

`needs-review` 不应自动安装。包被保留是为了让审查过程可复现，而不是推荐使用。

## 重新生成

```bash
python3 scripts/extract_community_skills.py
```

提取器只处理 `catalog.json` 中状态为 `selected-import` 且许可证在允许列表中的来源；翻译文档、测试夹具、vendor、缓存、重复内容、超大文件和超大包会被排除。
