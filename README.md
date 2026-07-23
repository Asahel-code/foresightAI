# ForeSightAI

ForeSightAI is an ontology-driven early warning and early action decision support platform for climate and disaster risk teams. It combines a web dashboard, a REST API, a knowledge graph, and reasoning workflows to help users turn environmental observations into explainable recommendations.

## Project purpose

ForeSightAI is designed to help teams:

- combine hazard, exposure, and vulnerability information,
- represent domain knowledge using ontologies and RDF,
- generate explainable recommendations for early actions,
- support regional expansion beyond a single pilot area.

## High-level architecture

- Frontend: Next.js + React + TypeScript + Tailwind + MapLibre
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Knowledge graph: RDF/Turtle files and ontology-driven reasoning
- Infrastructure: Docker Compose for local development

## Repository layout

- backend/: API, database models, reasoning services, RDF seeding
- frontend/: web application and map-based dashboard
- ontology/: ontology modules and domain vocabulary
- knowledge-graph/: generated RDF/Turtle graph files
- docs/: supporting documentation and design notes

## Quick start for a team

### 1. Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+ or Bun

### 2. Environment setup

Copy the example environment file if present and adjust values:

```bash
cp .env.example .env
```

### 3. Start the stack

```bash
docker compose up --build -d
```

This starts:

- Backend on http://localhost:8000
- Frontend on http://localhost:3000
- PostgreSQL on localhost:5432
- Redis on localhost:6379
- GraphDB on http://localhost:7200

### 4. Seed the database and knowledge graph

Run the backend ingestion and RDF export steps:

```bash
docker compose exec backend python app/db/ingest_pilot_data.py
docker compose exec backend python app/db/seed_rdf_graph.py
```

### 5. Open the application

Open the frontend UI at http://localhost:3000 and verify that the health endpoint responds at http://localhost:8000/api/v1/health.

## API conventions

The API is organized under a versioned prefix:

- /api/v1/health
- /api/v1/locations
- /api/v1/hazards
- /api/v1/recommendations

Use this prefix when integrating external tools or testing routes.

## Development workflow

1. Make changes in the relevant service.
2. Keep ontology and graph updates consistent with the data model.
3. Test backend logic before merging.
4. Review UI changes against the climate-service design goals.
5. Update documentation when new data sources or routes are introduced.

## Contribution guidelines

- Use clear commit messages.
- Keep changes scoped and documented.
- Maintain consistency between the RDF/ontology layer and the database layer.
- Add or update tests whenever new logic is introduced.

