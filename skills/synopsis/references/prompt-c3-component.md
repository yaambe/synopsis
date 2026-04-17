# Sub-agent prompt — C3 Component Diagram (per container)

Spawn one sub-agent per container identified in C2. `subagent_type: "general-purpose"`.

---

Your task: for the `<CONTAINER_NAME>` container in the repository at `<REPO_PATH>` (source rooted at
`<CONTAINER_SUBPATH>`), infer the internal logical modules and their relationships. Output a Mermaid `C4Component`
diagram.

What counts as a component:

- A logical grouping of files that fulfills one responsibility (routes, an auth middleware layer, a client to an
  external service, a background tool handler, a job orchestrator, a persistence layer, etc.).
- **Components are not files.** Multiple files often make up one component; a component is a concept, not a location.
- **Components are not functions.** If you are listing function-level entities you are too fine-grained; zoom out.

Evidence:

- The container's source tree. Directory names often reveal intent (`routes/`, `services/`, `middleware/`, `lib/`,
  `clients/`, `handlers/`).
- Import graph patterns: clusters of files that all import from the same boundary module usually indicate a component.
- Any pre-existing `ARCHITECTURE.md` or inline comments explaining structure.

Thinking-budget instructions — before emitting the diagram, list:

1. Every component you identified and a one-line justification.
2. Which file groups map to each component.
3. Relationships: who calls whom.

Output — one Mermaid block:

```mermaid
C4Component
    title Components — <Container Name>

    Container_Boundary(container, "<Container Name>") {
        Component(comp1, "Routes", "Framework", "HTTP entrypoints")
        Component(comp2, "Auth Middleware", "Library", "Token verification + RBAC")
        Component(comp3, "Classifier Service", "Module", "Business logic for X")
        ...
    }

    ContainerDb(db, "Postgres", "...")
    System_Ext(openrouter, "OpenRouter", "...")

    Rel(comp1, comp2, "Passes request through")
    Rel(comp1, comp3, "Calls for classification")
    Rel(comp3, db, "Reads/writes")
    Rel(comp3, openrouter, "Classification call", "HTTPS")
```

Target: 5–12 components per container. If you have more than 12, group them; if fewer than 3, the container is too small
for a C3 and you should say so in your reasoning (then emit an empty diagram with a note comment).
