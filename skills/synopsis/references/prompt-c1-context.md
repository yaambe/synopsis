# Sub-agent prompt — C1 System Context

Spawn with `subagent_type: "general-purpose"`.

---

Your task: infer the external human actors and external systems for the repository at `<REPO_PATH>`. Output a Mermaid
`C4Context` diagram that describes the product as a single `System_Boundary` talking to human users (`Person`) and
third-party systems (`System_Ext`).

Scope rules:

- **Include**: human roles (customer, admin, moderator, operator, etc.), third-party APIs the product calls (payment
  providers, AI APIs, email, OAuth, analytics, object storage, search providers, CDN, etc.).
- **Exclude**: internal services of the product itself — those belong in the C2 Container diagram, not here.
- **Ambiguous cases**: if a dependency is self-hosted alongside the product (e.g., Postgres the team runs), it's a C2
  container, not a C1 external system.

Evidence you should consult:

- `README.md` and any `docs/` architecture notes.
- Package manifests at the root and any obvious sub-project directories.
- Env-var references in code/config (often reveals which third parties the product integrates with — look for
  `*_API_KEY`, OAuth client IDs, SDK imports).
- Deploy configs (`Dockerfile`, `docker-compose.yml`, `vercel.json`, `render.yaml`, `fly.toml`).

Thinking-budget instructions — before emitting the diagram, explicitly list:

1. Which files you consulted and what you learned from each.
2. Which external systems you are certain about vs. inferring from weak evidence.
3. Any ambiguity you resolved and the rationale.

Output format — emit **only** the Mermaid diagram, inside a triple-backtick `mermaid` code block, nothing else:

```mermaid
C4Context
    title System Context — <Product Name>

    Person(role1, "Role Title", "One-line description")
    ...

    System_Boundary(product, "<Product Name>") {
        System(product_core, "<Product Name>", "One-line product description")
    }

    System_Ext(ext1, "<Third Party>", "What we use it for")
    ...

    Rel(role1, product_core, "Uses", "Channel")
    Rel(product_core, ext1, "Verb", "Protocol")
```

Keep the total node count ≤ 12 for legibility.
