# Vision image sizing — hard values and rationale

This file codifies the image-size constraints that matter when rendering diagrams for Claude to reason about. The
numbers come from Anthropic's published vision API documentation and from multimodal-LLM resolution research. Re-check
against Anthropic's docs if models or limits change.

## Anthropic's rules (authoritative for Claude)

Source: [Claude Vision — Anthropic API docs](https://platform.claude.com/docs/en/build-with-claude/vision).

| Rule             | Value                             | Effect                                                                                        |
| ---------------- | --------------------------------- | --------------------------------------------------------------------------------------------- |
| Token formula    | `tokens = (width × height) / 750` | Scales quadratically with pixels — every over-render is amplified in context cost             |
| Long edge ≤      | **1568 px**                       | Above this, Claude auto-downsamples before processing. Extra pixels cost latency, buy nothing |
| Total ≤          | **≈1.15 megapixels**              | Same: above this, auto-downsampled                                                            |
| Sweet spot (1:1) | **1092 × 1092**                   | ≈1590 tokens; Anthropic's stated balance of quality and cost                                  |
| Minimum edge     | **≥200 px**                       | Below this, output quality degrades                                                           |
| Hard rejection   | 8000 × 8000                       | API errors beyond                                                                             |
| Batch rule       | 2000 × 2000                       | When sending >20 images in one request, per-image limit drops to 2000 px                      |

**Key mental model**: going _over_ the recommended limits does not improve quality — Claude downsamples internally, so
you pay upload latency and extra tokens for content that gets discarded. Going _under_ 200 px on any edge _does_ hurt
quality. The sweet spot is "largest that doesn't trigger the internal downsample."

## Why this matters for diagrams specifically

Diagrams are text-dense images. OCR-flavored tasks benefit more from resolution than scene-understanding tasks up to a
saturation point (see [FastVLM, Apple MLR](https://machinelearning.apple.com/research/fast-vision-language-models) and
[Efficient Architectures for High-Resolution VLMs, arXiv 2501.02584](https://arxiv.org/html/2501.02584v1)). For diagrams
the saturation is around **896–1024 px long edge** based on ChartQA-class benchmarks — but the Anthropic-specific 1568
long-edge limit is the binding constraint for us, because anything bigger gets downsampled back below it.

Positional reasoning (arrows, loop boundaries, alt-else branches in sequence diagrams) is the motivating use case for
rendering at all. That reasoning depends on the renderer producing large-enough arrowheads and label text to survive the
Anthropic downsample. Rendering _at_ 1568 long edge preserves the most detail per pixel delivered; rendering _above_
1568 throws detail away in the downsample.

## Defaults chosen in this skill

`scripts/render.py` defaults:

```
WIDTH=1200
HEIGHT=900
```

- Total: 1.08 MP
- Tokens: ≈1440
- Long edge: 1200 (safely under 1568)

This sits at or just under every Anthropic recommended limit while leaving enough canvas for Mermaid's C4 and sequence
diagrams to render legible labels. It is the conservative default — suitable for any diagram type without per-type
tuning.

## Per-diagram-type optima (override with env vars)

If you know what you're rendering, the following are better:

| Diagram shape                    | WIDTH × HEIGHT | Megapixels | Tokens | Long edge | Notes                                                 |
| -------------------------------- | -------------- | ---------- | ------ | --------- | ----------------------------------------------------- |
| Square / C4Context / C4Container | 1092 × 1092    | 1.19 MP    | ≈1590  | 1092      | Anthropic's stated sweet spot                         |
| Wide (container, landscape)      | 1500 × 900     | 1.35 MP    | ≈1800  | 1500      | Slightly over 1.15 MP total but under long-edge limit |
| Tall (sequence, portrait)        | 900 × 1500     | 1.35 MP    | ≈1800  | 1500      | Same                                                  |
| Mixed / unknown                  | 1200 × 900     | 1.08 MP    | ≈1440  | 1200      | Default                                               |

Override with:

```bash
WIDTH=900 HEIGHT=1500 python3 scripts/render.py docs/c4/c4-declaration-pipeline.mmd
```

## When to deviate — print / publication mode

For paper figures, printed posters, or anything where a human will view the PNG directly at high DPI, the
Anthropic-tuned defaults are _too small_ — you'll see blurred text and jagged arrows when enlarged. Render separately
for print and **do not** Read the print-size PNG back into Claude's context.

Suggested print mode:

```bash
WIDTH=2400 HEIGHT=1800 BG=white python3 scripts/render.py paper/figures/
```

Do not then `Read` those PNGs — they exceed Anthropic limits and will be auto-downsampled with no benefit. Keep two
copies: the Claude-sized one (for in-session reasoning) and the print-sized one (for the figure file).

## Rules of thumb

1. **Longest edge ≤ 1568**, always, if the image will be Read by Claude.
2. **Never go under 200 px** on any edge.
3. For batch-rendering many diagrams, stay under ~1.15 MP per image to keep per-diagram tokens near the 1500-token sweet
   spot — at 8 diagrams per skill invocation, this keeps the total under ~12 K tokens.
4. **Don't optimize for "looks nice to humans" when rendering for Claude.** Those are different targets. Print at 2400+,
   reason at ≤1500.
5. If `mmdc` produces a PNG larger than the limit (Mermaid sometimes renders above the requested viewport for
   content-heavy diagrams), re-render with tighter WIDTH/HEIGHT env vars rather than post-processing.

## Sources

- [Claude Vision — Anthropic API docs](https://platform.claude.com/docs/en/build-with-claude/vision) — the authoritative
  source for token formula, size limits, and sweet-spot numbers.
- [AI Vision Input Limits — Awesome Agents](https://awesomeagents.ai/guides/ai-vision-image-resolution-limits/) —
  cross-provider limits comparison.
- [FastVLM — Apple Machine Learning Research](https://machinelearning.apple.com/research/fast-vision-language-models) —
  resolution/accuracy tradeoff analysis.
- [Efficient Architectures for High-Resolution Vision-Language Models, arXiv 2501.02584](https://arxiv.org/html/2501.02584v1)
  — diagram-resolution saturation evidence.
- [MME-RealWorld benchmark, arXiv 2408.13257](https://arxiv.org/html/2408.13257v1) — high-resolution multimodal
  benchmark motivating the "resolution matters for text-dense images" finding.
