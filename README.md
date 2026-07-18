# SKILLS

可复用的 Codex Skills 集合。

## 目录约定

所有可安装技能放在 `skills/<skill-name>/` 下，每个技能保持独立、标准的 Codex 结构：

```text
skills/
└── <skill-name>/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── scripts/
    └── references/
```

## 已收录技能

- [write-book](skills/write-book/)：使用分层上下文持续规划、研究、起草和修订小说或非虚构书稿。

## 安装单个技能

```bash
git clone https://github.com/userInner/SKILLS.git
cp -R SKILLS/skills/write-book "${CODEX_HOME:-$HOME/.codex}/skills/"
```

重启 Codex 或新建任务后，通过 `$write-book` 调用。
