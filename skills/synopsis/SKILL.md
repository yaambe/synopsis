---
name: synopsis
description: >-
  Use this skill to produce architecture documentation for a repository as Mermaid C4 diagrams (system context,
  containers, components, sequence flows) written as `.mmd` files with rendered PNGs. Trigger whenever the user wants to
  map out, document, visualize, or explain a codebase's architecture — services, containers, modules, and how requests
  or jobs flow — especially for onboarding, README/architecture docs, or understanding an unfamiliar repo. Trigger even
  without the word "C4": phrases like "document the architecture", "diagram the services", "show how it hangs together",
  "context/container/component breakdown", or "sequence for the X flow" all qualify. Also use to refresh a single
  existing C4 diagram against current source, generate just one level (e.g. context-only), or re-render existing `.mmd`
  files to PNG. Do NOT use for standalone flowcharts, gantt/class/ER/UML diagrams, DB schema visualizations, dependency
  graphs, or non-Mermaid formats (PlantUML, Graphviz).
allowed-tools: [Read, Write, Bash, Glob, Grep, Agent]
---

# synopsis

Generates a C4 diagram set as `.mmd` files and renders them to PNG in one pass.

The user invoked this with: $ARGUMENTS

**Requires:** Node.js (for `mmdc` via `npx`).

## Output set

| File                           | Level | Content                             |
| ------------------------------ | ----- | ----------------------------------- |
| `c1-system-context.mmd`        | C1    | External actors + external systems  |
| `c2-container.mmd`             | C2    | Deployable units and relationships  |
| `c3-component-<container>.mmd` | C3    | Internal modules per container      |
| `c4-<pipeline>-pipeline.mmd`   | C4    | Sequence diagram per major pipeline |
| `*.png`                        | —     | Rendered image next to each `.mmd`  |
| `README.md`                    | —     | Index of diagrams                   |

## Output directory resolution

Resolve `<OUTDIR>` once, up front:

1. **User-specified.** If `$ARGUMENTS` names an output dir (e.g. `/synopsis path/to/dir` or `out=path/to/dir`), use it
   verbatim.
2. **No args, no existing `docs/`.** Use `<repo>/docs/c4/`.
3. **No args, `<repo>/docs/` already exists.** STOP and ask the user before writing anything. Use exactly this prompt:
   `"<repo>/docs/ already exists. Where should I put the C4 diagrams? Give me a path, or reply 'auto' for <repo>/diagrams/c4/."`
   Wait for the user's reply. Do not proceed until they answer. On `auto`, use `<repo>/diagrams/c4/`.

State the chosen `<OUTDIR>` to the user before writing.

## Workflow

1. **Recon.** `python3 scripts/recon.py <repo>`. Identify **containers** (deployable units) and **pipelines** (major
   request/job flows).

2. **Launch sub-agents in parallel.** One message, multiple `Agent` calls, `subagent_type: "general-purpose"`. For each
   diagram, `Read` the matching template under `references/` (`prompt-c1-context.md`, `prompt-c2-container.md`,
   `prompt-c3-component.md` once per container, `prompt-c4-dataflow.md` once per pipeline), substitute `<REPO_PATH>` and
   any per-container/pipeline fields, prepend the recon report, and pass the result as the sub-agent's prompt.

3. **Write.** `mkdir -p <OUTDIR>`, write each `.mmd`. Defer `README.md` until the architecture review step.

4. **Lint.** `python3 scripts/lint.py <OUTDIR>`. The script validates directives and `UpdateLayoutConfig`. Re-run any
   failed sub-agent.

5. **Render to PNG.** `python3 scripts/render.py <OUTDIR>` — the script auto-picks size per diagram (see Render sizing
   below for the table). Skip only if `$ARGUMENTS` contains `--no-render`. If the render fails because Node/`mmdc` is
   unavailable, report it to the user and stop — do **not** attempt a global install.

6. **Architecture review.** `Read` every PNG in `<OUTDIR>` so the visual tokens are in context. You already have the
   recon report and know the containers/pipelines — use that combined context to analyze the diagrams for architectural
   issues: single points of failure, circular dependencies, missing error/retry paths, security boundaries that look
   wrong (e.g. a public-facing container talking directly to a database with no intermediary), over-coupled components,
   and design smells. For each finding, read the relevant source code under `<REPO_PATH>` to confirm or refute it.
   Present findings as a markdown table with columns: **#**, **Issue**, **Severity** (high / medium / low), **Diagram
   evidence**, **Code evidence**, **Status** (confirmed / unconfirmed / refuted). Write the indexing `README.md` with
   the diagram list and append the review table under a `## Architecture review` heading. Output the review table to the
   user in the conversation.

## Single-level mode

When the user asks for just one level (e.g. "just the context diagram", "only the C2", "sequence for the checkout
flow"): run recon, then launch only the relevant sub-agent(s). Lint, write, render as usual. Skip the architecture
review — it needs the full picture to be useful.

## Refresh mode

When the user names one specific diagram to update (e.g. "update the c2 container diagram", "refresh the ingest
pipeline diagram"): read the existing `.mmd`, launch **one** sub-agent with the matching template, prepended with:

> Refresh mode. The current diagram is below — treat it as a starting point, not as truth. Read the relevant source
> under `<REPO_PATH>` and emit an updated diagram. Preserve naming conventions unless the code has clearly renamed
> things.
>
> ```mermaid
> <paste current .mmd>
> ```

Lint, write back, re-render. Skip the architecture review for single-diagram refreshes. If the user says "redo the
architecture diagrams" without naming one, run the full flow.

## Render-only mode

If the user wants to re-render an existing C4 `.mmd` set (no recon, no sub-agents): jump straight to step 5 (render).
Skip the architecture review. Non-C4 diagrams are out of scope — decline and point them elsewhere.

```bash
python3 scripts/render.py path/to/diagram.mmd    # single file
python3 scripts/render.py path/to/dir/           # whole directory
```

If no path is given, search in order: `$ARGUMENTS` → `<repo>/diagrams/c4/` → `<repo>/docs/c4/`. If none exist, no `.mmd`
set yet — run the full flow.


Auto-picked per diagram from the first directive:

| First directive   | WIDTH × HEIGHT |
| ----------------- | -------------- |
| `C4Context`       | 1092 × 1092    |
| `C4Container`     | 1500 × 900     |
| `C4Component`     | 1500 × 900     |
| `sequenceDiagram` | 900 × 1500     |
| anything else     | 1200 × 900     |

All sizes stay under Anthropic's 1568 px long-edge limit. Wide/tall variants slightly exceed the ~1.15 MP recommendation
and may be lightly downsampled, but this has no meaningful impact on diagram legibility. Env overrides: `WIDTH`, `HEIGHT`,
`BG` (default `white`), `THEME` (default `default`). Batch mode is best-effort; script exits 1 if any file failed.

## When NOT to use

- Single-file scripts or tiny repos.
- Non-C4 sequence diagrams (login flows, API call traces) that aren't tied to a C4 pipeline — C4 pipeline sequences
  *are* in scope.
- Publication-grade C4 figures — Mermaid's C4 renderer is cramped; use Structurizr or PlantUML.
- Interactive viewing (use a browser).

## References

- `scripts/recon.py`, `scripts/lint.py`, `scripts/render.py`
- `references/prompt-c{1,2,3,4}-*.md` — sub-agent prompt templates
- `references/vision-image-sizing.md` — sizing rationale + troubleshooting
