# Backend README

This backend service powers the ForeSightAI API, database layer, reasoning engine, and RDF knowledge-graph pipeline.

## Purpose

The backend is responsible for:

- exposing REST endpoints for locations, hazards, and recommendations,
- storing structured data in PostgreSQL,
- generating and exporting RDF/Turtle graphs for the knowledge layer,
- supporting explainable reasoning over hazard, exposure, and vulnerability evidence.

## Technology stack

- FastAPI
- SQLAlchemy
- PostgreSQL + PostGIS
- Redis
- RDFlib for RDF export
- Pydantic models and schemas

## Project structure

- app/main.py: FastAPI application entry point
- app/api/routes/: route definitions for the public API
- app/models/: SQLAlchemy models
- app/services/: reasoning, RDF utilities, and support services
- app/db/: database bootstrapping, ingestion, and graph seeding
- app/core/: configuration and environment loading

## Local development

### With Docker Compose

The recommended workflow is to run the full stack with Docker:

```bash
docker compose up --build -d
```

### Running backend commands

Inside the running container:

```bash
docker compose exec backend bash
```

Useful commands:

```bash
python app/db/ingest_pilot_data.py
python app/db/seed_rdf_graph.py
```

### Environment variables

The backend reads configuration from the project-level .env file. Key values include:

- DATABASE_URL
- REDIS_URL
- GRAPHDB_URL
- OPENAI_API_KEY

## API routes

The backend exposes versioned endpoints under:

- /api/v1/health
- /api/v1/locations
- /api/v1/hazards
- /api/v1/recommendations

## Knowledge graph workflow

The RDF graph is generated from the database and stored under the knowledge-graph directory. This makes it possible to support multiple regions by using country-specific namespace and URI patterns.

## Testing

Run the backend tests with:

```bash
pytest -q
```

## Notes for ICPAC-style operations

Keep the backend logic transparent and evidence-based. When adding new regions, hazards, or indicators, ensure the ontology, database records, and RDF export remain aligned.
