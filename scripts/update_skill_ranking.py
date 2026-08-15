#!/usr/bin/env python3
"""Refresh the GitHub Agent Skill source index using only the standard library."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

API = "https://api.github.com"
MINIMUM_STARS = 300
SEARCH_QUERIES = (
    "topic:agent-skills archived:false",
    "topic:claude-skills archived:false",
    "topic:codex-skills archived:false",
    '"agent skills" in:name,description,readme archived:false',
    '"SKILL.md" in:readme archived:false',
)


class GitHubAPI:
    def __init__(self, token: str) -> None:
        if not token:
            raise ValueError("GITHUB_TOKEN is required")
        self.token = token

    def request(self, path: str, *, method: str = "GET", payload: dict | None = None) -> dict:
        body = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(
            API + path,
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "userInner-SKILLS-indexer/1.0",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    return json.load(response)
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    return {}
                if error.code in (403, 429):
                    reset = error.headers.get("X-RateLimit-Reset", "unknown")
                    raise RuntimeError(f"GitHub rate limit reached; reset={reset}") from error
                if error.code < 500 or attempt == 2:
                    detail = error.read(2048).decode(errors="replace")
                    raise RuntimeError(f"GitHub returned HTTP {error.code}: {detail}") from error
            except urllib.error.URLError as error:
                if attempt == 2:
                    raise RuntimeError(f"GitHub request failed: {error.reason}") from error
            time.sleep(2**attempt)
        raise RuntimeError("GitHub request failed")

    def refresh_existing(self, repositories: list[dict]) -> dict[str, dict]:
        refreshed: dict[str, dict] = {}
        for offset in range(0, len(repositories), 40):
            batch = repositories[offset : offset + 40]
            aliases: list[str] = []
            alias_names: dict[str, str] = {}
            for index, source in enumerate(batch):
                owner, name = source["repository"].split("/", 1)
                alias = f"r{index}"
                alias_names[alias] = source["repository"].lower()
                aliases.append(
                    f'{alias}: repository(owner:{json.dumps(owner)}, name:{json.dumps(name)}) '
                    "{ nameWithOwner url description isArchived stargazerCount "
                    "defaultBranchRef { name } licenseInfo { spdxId } }"
                )
            response = self.request("/graphql", method="POST", payload={"query": "query {" + " ".join(aliases) + "}"})
            if response.get("errors"):
                raise RuntimeError(f"GraphQL refresh failed: {response['errors']}")
            for alias, repo in response.get("data", {}).items():
                if repo:
                    refreshed[alias_names[alias]] = repo
        return refreshed

    def discover(self, minimum_stars: int) -> dict[str, dict]:
        discovered: dict[str, dict] = {}
        for query in SEARCH_QUERIES:
            qualified = f"{query} stars:>{minimum_stars}"
            for page in range(1, 11):
                params = urllib.parse.urlencode(
                    {"q": qualified, "sort": "stars", "order": "desc", "per_page": 100, "page": page}
                )
                response = self.request(f"/search/repositories?{params}")
                if response.get("incomplete_results"):
                    raise RuntimeError(f"GitHub returned incomplete search results for {query!r}")
                items = response.get("items", [])
                for repo in items:
                    discovered[repo["full_name"].lower()] = repo
                if len(items) < 100:
                    break
                time.sleep(2.1)
        return discovered

    def skill_files(self, repository: str, branch: str) -> tuple[int, bool]:
        endpoint = f"/repos/{repository}/git/trees/{urllib.parse.quote(branch, safe='')}?recursive=1"
        response = self.request(endpoint)
        if not response:
            return 0, False
        count = sum(
            1
            for item in response.get("tree", [])
            if item.get("type") == "blob" and PurePosixPath(item.get("path", "")).name.lower() == "skill.md"
        )
        return count, bool(response.get("truncated"))


def update_index(current: dict, api: GitHubAPI, minimum_stars: int) -> dict:
    previous = {item["repository"].lower(): item for item in current["repositories"]}
    existing_metadata = api.refresh_existing(current["repositories"])
    discovered_metadata = api.discover(minimum_stars)
    repositories: list[dict] = []
    new_count = 0

    for key in sorted(set(existing_metadata) | set(discovered_metadata)):
        repo = discovered_metadata.get(key) or existing_metadata[key]
        stars = int(repo.get("stargazers_count", repo.get("stargazerCount", 0)))
        archived = bool(repo.get("archived", repo.get("isArchived", False)))
        if archived or stars <= minimum_stars:
            continue
        old = previous.get(key)
        if old:
            repositories.append(merge_existing(old, repo, stars))
            continue
        branch = repo.get("default_branch") or (repo.get("defaultBranchRef") or {}).get("name")
        if not branch:
            continue
        count, truncated = api.skill_files(repo_name(repo), branch)
        if count == 0:
            continue
        repositories.append(new_source(repo, stars, branch, count, truncated))
        new_count += 1

    repositories.sort(key=lambda item: (-item["stars"], item["repository"].lower()))
    for rank, item in enumerate(repositories, 1):
        item["rank"] = rank
    return {
        "snapshotDate": datetime.now(UTC).date().isoformat(),
        "sort": "githubStarsDescending",
        "minimumStarsExclusive": minimum_stars,
        "repositoryCount": len(repositories),
        "repositoriesWithSkillFiles": sum(item["skillFileCount"] > 0 for item in repositories),
        "newlyDiscoveredCount": new_count,
        "directSkillCount": int(current.get("directSkillCount", 0)),
        "repositories": repositories,
    }


def merge_existing(old: dict, repo: dict, stars: int) -> dict:
    item = dict(old)
    item.update(
        repository=repo_name(repo),
        stars=stars,
        url=repo.get("html_url") or repo.get("url") or old.get("url", ""),
        description=repo.get("description") or "",
        defaultBranch=repo.get("default_branch") or (repo.get("defaultBranchRef") or {}).get("name") or old.get("defaultBranch", "main"),
        license=license_id(repo),
    )
    item.pop("rank", None)
    return item


def new_source(repo: dict, stars: int, branch: str, count: int, truncated: bool) -> dict:
    description = repo.get("description") or ""
    text = f"{repo_name(repo)} {description}".lower()
    kind = "standalone-skill" if count == 1 else "skill-collection" if "skill" in text else "project-with-skills"
    item = {
        "repository": repo_name(repo),
        "stars": stars,
        "license": license_id(repo),
        "url": repo.get("html_url") or repo.get("url") or f"https://github.com/{repo_name(repo)}",
        "description": description,
        "defaultBranch": branch,
        "skillFileCount": count,
        "kind": kind,
        "qualification": "contains-skill-file",
        "status": "index-only",
        "reason": "license-not-detected" if license_id(repo) == "NOASSERTION" else "awaiting-manual-review",
    }
    if truncated:
        item["treeTruncated"] = True
    return item


def repo_name(repo: dict) -> str:
    return repo.get("full_name") or repo.get("nameWithOwner") or ""


def license_id(repo: dict) -> str:
    value = repo.get("license") or repo.get("licenseInfo") or {}
    return value.get("spdx_id") or value.get("spdxId") or "NOASSERTION"


def render_ranking(index: dict, limit: int | None = None) -> str:
    items = index["repositories"] if limit is None else index["repositories"][:limit]
    lines = [
        "# GitHub Agent Skills Star 排名" if limit is None else "## 高星来源索引",
        "",
        f"快照日期 **{index['snapshotDate']}**。共收录 **{index['repositoryCount']}** 个超过 {index['minimumStarsExclusive']} Star 的来源，"
        f"其中 **{index['repositoriesWithSkillFiles']}** 个已核验包含 `SKILL.md`。Star 会变化，排名不代表安全或质量背书。",
        "",
        "自动发现只进入索引；许可证、依赖、权限和隔离测试通过后，才可能进入直装目录。",
        "",
        "| 排名 | 项目 | Stars | 许可证 | SKILL.md 数 | 本仓库状态 |",
        "|---:|---|---:|---|---:|---|",
    ]
    for item in items:
        license_name = "未识别" if item.get("license") in (None, "", "NOASSERTION") else item["license"]
        lines.append(
            f"| {item['rank']} | [{item['repository']}]({item['url']}) | {item['stars']:,} | "
            f"{license_name} | {item['skillFileCount']} | {status_label(item)} |"
        )
    return "\n".join(lines) + "\n"


def status_label(item: dict) -> str:
    if item.get("status") == "selected-import":
        return "已精选导入"
    return {
        "license-not-detected": "索引，许可证未识别",
        "awaiting-manual-review": "索引，待人工审查",
        "project-bundled-skills": "索引，项目附带 Skill",
        "large-skill-collection-review-pending": "索引，Skill 集合待审查",
        "framework-coupled": "索引，框架耦合",
        "agent-framework-coupled": "索引，Agent 框架耦合",
    }.get(item.get("reason"), "索引")


def update_readme(path: Path, index: dict) -> None:
    text = path.read_text()
    start = text.index("## 高星来源索引")
    end = text.index("\n## ", start + 3)
    summary = render_ranking(index, limit=50).rstrip()
    path.write_text(text[:start] + summary + "\n\n" + text[end + 1 :])


def write_outputs(root: Path, index: dict) -> None:
    (root / "catalog.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    (root / "RANKING.md").write_text(render_ranking(index))
    update_readme(root / "README.md", index)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--render-only", action="store_true", help="validate rendering without calling GitHub")
    args = parser.parse_args()
    catalog = json.loads((args.root / "catalog.json").read_text())
    if args.render_only:
        render_ranking(catalog)
        print(f"validated {len(catalog['repositories'])} repositories")
        return 0
    api = GitHubAPI(os.environ.get("GITHUB_TOKEN", "").strip())
    updated = update_index(catalog, api, int(catalog.get("minimumStarsExclusive", MINIMUM_STARS)))
    if not updated["repositories"]:
        raise RuntimeError("refusing to publish an empty index")
    write_outputs(args.root, updated)
    print(f"updated {updated['repositoryCount']} repositories; new={updated['newlyDiscoveredCount']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # GitHub Actions needs one concise terminal error.
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
