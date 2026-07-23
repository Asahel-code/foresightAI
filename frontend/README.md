# Frontend README

The frontend provides the web interface for ForeSightAI, including the map-driven dashboard, location selection, hazard summary, and reasoning panel.

## Purpose

The frontend helps users:

- explore locations and hazards visually,
- view early-warning evidence and recommendations,
- interact with geospatial information in a simple, climate-service-friendly interface.

## Technology stack

- Next.js
- React
- TypeScript
- Tailwind CSS
- MapLibre GL
- Axios for API requests

## Project structure

- app/: routing and top-level page layout
- components/: reusable UI components such as the map, selector, and reasoning panel
- lib/: API client helpers and shared frontend logic
- public/: static assets

## Local development

### With Docker Compose

The simplest route is:

```bash
docker compose up --build -d
```

Then open:

- http://localhost:3000

### Local frontend commands

If you want to run the frontend outside Docker:

```bash
cd frontend
npm install
npm run dev
```

If you prefer Bun, the same scripts should work with Bun as well.

## API integration

The frontend reaches the backend through the versioned API prefix:

```ts
/api/v1/locations
/api/v1/hazards
/api/v1/recommendations
```

## Notes

When adding new frontend features, keep the map, alert summary, and reasoning evidence aligned so users can quickly understand what triggered a recommendation.
