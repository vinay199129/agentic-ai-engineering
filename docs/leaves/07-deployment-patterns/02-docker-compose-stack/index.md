!!! info "`07-deployment-patterns/02-docker-compose-stack`"
    📓 [Open the notebook](notebook.ipynb)  
    💻 [View source on GitHub](https://github.com/vinay199129/agentic-ai-engineering/tree/main/07-deployment-patterns/02-docker-compose-stack)

**Headline metrics:** _no headline metric_

# Docker Compose stack — local agent dev environment

**Problem:** Real agents touch several services: an HTTP API, a vector store, a tracing backend, a cache/queue. Wiring these up by hand on every laptop wastes hours and breeds drift. **Docker Compose** gives every contributor an identical, one-command stack that mirrors prod's service topology — without paying cloud costs to iterate.

**What you'll learn:**
- A working multi-service compose with the four pieces every agentic stack wants:
  - `api` — your FastAPI agent (re-uses leaf 00's app)
  - `postgres` (pgvector) — vectors + Langfuse storage
  - `redis` — cache + pub/sub for SSE fan-out
  - `langfuse` — local tracing UI on `:3000`
- Healthchecks so `depends_on: condition: service_healthy` blocks `api` until Postgres is ready.
- Named volumes for durable Postgres/Redis state across `down`/`up`.
- The trick of bind-mounting code into the `api` container so iteration doesn't rebuild the image.

**When to use it:** Local dev for any agent that talks to ≥2 stateful services.

**When NOT to use it:** Production. Use a managed service or Kubernetes once you're past 1 box.

## Run it

```powershell
# Validate the YAML offline:
uv run python 07-deployment-patterns/02-docker-compose-stack/eval.py

# Bring the stack up (requires Docker Desktop):
docker compose -f 07-deployment-patterns/02-docker-compose-stack/compose.yaml up -d
# Hit it:
curl http://localhost:8000/healthz
# Open the tracing UI:
start http://localhost:3000
```

## Key results

The eval parses `compose.yaml`, asserts the four required services are
present with the expected image / port / healthcheck shape, and that
volumes + dependency-conditions are wired correctly. Tracked metrics:
`yaml_parses`, `required_services_present`, `healthcheck_coverage`,
`depends_on_uses_health_condition`.

## References

- [Compose spec — healthcheck](https://github.com/compose-spec/compose-spec/blob/main/spec.md#healthcheck)
- [pgvector image](https://hub.docker.com/r/pgvector/pgvector)
- [Langfuse self-host](https://langfuse.com/self-hosting)
