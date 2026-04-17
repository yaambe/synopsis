# Sub-agent prompt — C2 Container Diagram

Spawn with `subagent_type: "general-purpose"`.

---

Your task: infer the deployable units (containers) of the product at `<REPO_PATH>` and their relationships. Output a
Mermaid `C4Container` diagram.

Container types to distinguish:

- `Container(...)` — internal deployable units (frontend SPA, API backend, background worker, etc.).
- `ContainerDb(...)` — persistent data stores (Postgres, MongoDB, SQLite, etc.).
- `Container_Ext(...)` — external but dedicated infrastructure (S3-compatible object storage, a self-hosted queue,
  managed cache).
- `System_Ext(...)` — third-party SaaS the product calls (already in C1; include only the ones that containers talk to
  directly).

Evidence:

- Top-level directories that each carry their own manifest → almost certainly separate containers. Look for any of:
  - JS/TS: `package.json`
  - Python: `pyproject.toml`, `setup.py`, `requirements.txt`
  - Go: `go.mod`
  - Rust: `Cargo.toml`
  - JVM: `pom.xml`, `build.gradle`, `build.gradle.kts`
  - .NET: `*.csproj`, `*.fsproj`
  - Ruby: `Gemfile`
  - PHP: `composer.json`
  - Elixir: `mix.exs`
- `Dockerfile`, `docker-compose.yml` / `compose.yml`, process managers (`Procfile`, `ecosystem.config.js`).
- Deploy config files (`vercel.json`, `fly.toml`, `render.yaml`, `netlify.toml`, `app.yaml`, `serverless.yml`,
  `kustomization.yaml`, `.github/workflows/deploy-*.yml`).
- Framework conventions (Next.js `api/` dir, NestJS `main.ts`, FastAPI `main.py`, Spring Boot `Application.java`,
  ASP.NET `Program.cs`, Phoenix `application.ex`, etc.).

Thinking-budget instructions — before emitting the diagram, list:

1. Containers identified and evidence per container.
2. Which ones are self-hosted by the team vs. managed SaaS.
3. Relationships you are inferring from imports vs. seeing in explicit config.

Output — one Mermaid block, no prose:

```mermaid
C4Container
    title Container Diagram — <Product Name>

    Person(role1, "Role Title", "...")

    System_Boundary(product, "<Product Name>") {
        Container(frontend, "Frontend SPA", "Tech stack", "Role description")
        Container(api, "API Backend", "Tech stack", "Role description")
        ...
    }

    ContainerDb(db, "Postgres", "PostgreSQL", "...")
    Container_Ext(storage, "S3", "S3-compatible", "...")
    System_Ext(thirdparty1, "<SaaS>", "What it does")

    Rel(role1, frontend, "Uses", "HTTPS")
    Rel(frontend, api, "Calls", "HTTPS/JSON")
    Rel(api, db, "Reads/writes", "Postgres")
    ...

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

The `UpdateLayoutConfig` line at the end is important — without it Mermaid's C4 renderer lays boxes out one-per-row and
the result is unusable.
