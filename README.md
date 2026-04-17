# synopsis

An agentic skill that generates C4 architecture diagrams from any codebase and uses vision to review them for architectural vulnerabilities.

## Why this exists

This is a proof of concept exploring what happens when you combine LLM multimodality with architectural reasoning. The idea is simple: have the model read your code, produce C4 diagrams (system context, containers, components, data flows), render them to PNG, then *read the diagrams back* using vision to reason about the architecture at a structural level.

The results have been surprisingly useful. We've found real architectural vulnerabilities across multiple projects this way, things like missing security boundaries between public-facing containers and databases, single points of failure, circular dependencies, and error paths that don't exist. These are hard to spot reading code file-by-file but become obvious when you look at the picture.

## What it produces

| File | Level | Content |
|------|-------|---------|
| `c1-system-context.mmd` | C1 | External actors and third-party systems |
| `c2-container.mmd` | C2 | Deployable units and their relationships |
| `c3-component-<name>.mmd` | C3 | Internal modules per container |
| `c4-<name>-pipeline.mmd` | C4 | Sequence diagram per major data flow |
| `*.png` | - | Rendered image for each `.mmd` |
| `README.md` | - | Diagram index + architecture review table |

The architecture review at the end is the interesting part. It reads every rendered PNG alongside the source code and flags confirmed issues with severity, diagram evidence, and code evidence.

## Installation

```bash
npx skills add yaambe/synopsis
```

Or manually copy the skill into your skills directory:

```bash
# Clone the repo
git clone https://github.com/yaambe/synopsis.git

# Copy to your skills directory
cp -r synopsis/skills/synopsis ~/.claude/skills/
```
or
```bash
cp -r synopsis/skills/synopsis ~/.agents/skills/
```

After installation, restart your agent. The skill will be available as `/synopsis` in any project.

## Requirements

- **Node.js** for Mermaid CLI (`mmdc` via `npx`)
- **Python 3** for the recon, lint, and render scripts
- **Optional:** ImageMagick (`mogrify` + `identify`) or macOS `sips` for post-render resizing

## Usage

You can invoke the skill via slash command. This is the recommended way. Simply asking tends to under trigger it.
```
/synopsis
```

You can also target specific levels or refresh existing diagrams:
```
> just the context diagram
> update the c2 container diagram
> render the existing .mmd files in docs/c4/ to PNG
```

## How it works

1. **Recon** - `scripts/recon.py` scans the repo for manifests, deploy configs, entry points, and existing docs to identify containers and candidate pipelines.

2. **Parallel sub-agents** - One agent per diagram, each with a specialized prompt template from `references/`. They read the actual source code and emit Mermaid `.mmd` files.

3. **Lint** - `scripts/lint.py` validates structural correctness (missing directives, leftover code fences, missing `UpdateLayoutConfig`).

4. **Render** - `scripts/render.py` converts `.mmd` to PNG with sizes tuned for vision input limits (long edge <= 1568px, ~1.15MP).

5. **Architecture review** - The agent reads every rendered PNG back using vision, cross-references with the source code, and produces a findings table with confirmed/unconfirmed issues.
