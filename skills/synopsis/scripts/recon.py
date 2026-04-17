#!/usr/bin/env python3
"""Emit a markdown recon report for a repository -- input to synopsis sub-agents.

Scans for evidence of deployable units (containers) and entry points
(candidate pipelines). The main agent passes the report to every parallel
sub-agent so they share canonical container names and don't independently
re-discover the same files.

Usage:
  recon.py <repo_path>

Writes the report to stdout. Pipe or capture as needed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PRUNE_PARTS = {
    "node_modules", "vendor", ".git", "target", "dist", "build",
    ".next", ".venv", "__pycache__",
}

MANIFESTS = {
    "package.json", "pyproject.toml", "setup.py", "requirements.txt",
    "go.mod", "Cargo.toml", "pom.xml",
    "build.gradle", "build.gradle.kts",
    "Gemfile", "composer.json", "mix.exs",
}
MANIFEST_GLOBS = ("*.csproj", "*.fsproj")

DEPLOY_FILES = {
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml", "Procfile",
    "fly.toml", "render.yaml", "vercel.json", "netlify.toml",
    "app.yaml", "serverless.yml", "serverless.yaml", "kustomization.yaml",
}
DEPLOY_GLOBS = ("Dockerfile.*",)

K8S_DIR_NAMES = {"k8s", "kubernetes", "helm", "charts"}

ENTRY_FILENAMES = {
    "main.py", "app.py", "server.py", "wsgi.py", "asgi.py",
    "main.ts", "main.js", "server.ts", "server.js",
    "index.ts", "index.js",
    "main.go", "main.rs",
}
ENTRY_DIR_NAMES = {
    "routes", "handlers", "api", "controllers",
    "jobs", "workers", "tasks", "cron", "consumers",
}
ENTRY_SUFFIXES = {
    ".py", ".ts", ".js", ".go", ".rs",
    ".java", ".kt", ".rb", ".cs", ".ex", ".exs",
}
TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec"}

DOC_PATTERNS = re.compile(r"^(readme|architecture|design)", re.IGNORECASE)

DEPLOY_WORKFLOW_RE = re.compile(r"deploy|release|publish|ship", re.IGNORECASE)


def is_pruned(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in PRUNE_PARTS for part in rel.parts)


def walk(root: Path, max_depth: int):
    """Yield files up to max_depth below root, skipping pruned dirs."""
    root = root.resolve()

    def _walk(d: Path, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(d.iterdir())
        except (OSError, PermissionError):
            return
        for entry in entries:
            if entry.name in PRUNE_PARTS:
                continue
            if entry.is_symlink():
                continue
            if entry.is_file():
                yield entry
            elif entry.is_dir():
                yield from _walk(entry, depth + 1)

    yield from _walk(root, 1)


def print_section(title: str) -> None:
    print(f"## {title}")
    print()


def print_list_or_empty(items: list[Path], root: Path) -> None:
    if items:
        for item in items:
            try:
                rel = item.relative_to(root)
            except ValueError:
                rel = item
            print(f"  - {rel}")
    else:
        print("  _(none found)_")
    print()


def find_manifests(root: Path) -> list[Path]:
    out = []
    for f in walk(root, 4):
        if f.name in MANIFESTS or any(f.match(g) for g in MANIFEST_GLOBS):
            out.append(f)
    return sorted(out)


def find_deploy(root: Path) -> list[Path]:
    out = []
    for f in walk(root, 4):
        if f.name in DEPLOY_FILES or any(f.match(g) for g in DEPLOY_GLOBS):
            out.append(f)
    return sorted(out)


def find_k8s(root: Path) -> list[Path]:
    out = []

    def _walk_dirs(d: Path, depth: int):
        if depth > 5:
            return
        try:
            entries = sorted(d.iterdir())
        except (OSError, PermissionError):
            return
        for entry in entries:
            if entry.name in PRUNE_PARTS or entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in K8S_DIR_NAMES:
                    out.append(entry)
                _walk_dirs(entry, depth + 1)

    _walk_dirs(root.resolve(), 1)
    return sorted(out)


def find_entry_points(root: Path, limit: int = 60) -> list[Path]:
    out = []
    for f in walk(root, 6):
        parts = set(f.parts)
        if parts & TEST_DIR_NAMES:
            continue
        if f.name in ENTRY_FILENAMES:
            out.append(f)
            continue
        if f.suffix in ENTRY_SUFFIXES and any(p in ENTRY_DIR_NAMES for p in f.parts):
            out.append(f)
    out.sort()
    return out[:limit]


def find_docs(root: Path, limit: int = 30) -> list[Path]:
    out = []
    for f in walk(root, 4):
        if f.suffix == ".mmd":
            continue
        if DOC_PATTERNS.match(f.stem) or "docs" in f.parts:
            out.append(f)
    out.sort()
    return out[:limit]


def find_existing_mmd(root: Path) -> list[Path]:
    return sorted(f for f in walk(root, 5) if f.suffix == ".mmd")


def find_deploy_workflows(root: Path) -> list[Path] | None:
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.is_dir():
        return None
    out = []
    try:
        for entry in sorted(wf_dir.iterdir()):
            if entry.is_file() and DEPLOY_WORKFLOW_RE.search(entry.name):
                out.append(entry)
    except OSError:
        return []
    return out


def top_level_layout(root: Path, limit: int = 60) -> list[str]:
    out = []
    try:
        for entry in sorted(root.iterdir()):
            name = entry.name
            if entry.is_dir():
                name += "/"
            elif entry.is_symlink():
                name += "@"
            elif entry.is_file() and (entry.stat().st_mode & 0o111):
                name += "*"
            out.append(name)
    except OSError:
        pass
    return out[:limit]


USAGE = "usage: recon.py <repo_path>\n"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write(USAGE)
        return 2
    repo = Path(argv[1])
    if not repo.is_dir():
        sys.stderr.write(USAGE)
        return 2

    repo = repo.resolve()

    print(f"# Recon — {repo.name}")
    print()
    print("_Generated by synopsis recon. Pass this report to each C-level sub-agent_")
    print("_so they share canonical container names and don't re-discover the same files._")
    print()

    print_section("Top-level layout")
    print("```")
    for line in top_level_layout(repo):
        print(line)
    print("```")
    print()

    print_section("Manifests (each one with its own manifest is a candidate container)")
    print_list_or_empty(find_manifests(repo), repo)

    print_section("Containerization / deploy configs")
    print_list_or_empty(find_deploy(repo), repo)

    print_section("Kubernetes / Helm manifests")
    print_list_or_empty(find_k8s(repo), repo)

    print_section("CI deploy hints")
    workflows = find_deploy_workflows(repo)
    if workflows is None:
        print("  _(no .github/workflows)_")
        print()
    else:
        print_list_or_empty(workflows, repo)

    print_section("Likely entry points (candidate pipelines)")
    print("_Route handlers, job entry points, cron, queue consumers — each is a candidate pipeline._")
    print()
    print_list_or_empty(find_entry_points(repo), repo)

    print_section("Architecture docs already in repo")
    print_list_or_empty(find_docs(repo), repo)

    print_section("Existing C4 diagrams (if any) — refresh-mode priors")
    print_list_or_empty(find_existing_mmd(repo), repo)

    print("---")
    print("_End recon. Sub-agents should still verify by reading these files; "
          "recon is a head start, not the source of truth._")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
