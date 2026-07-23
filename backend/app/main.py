from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine, Base, get_db

from app.api.routes import locations, hazards, recommendations

API_PREFIX = "/api/v1"

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="ForeSightAI - Ontology-Driven Early Warning and Early Action Decision Intelligence Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if not existing).")


@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down...")


@app.get("/health", tags=["Health Check"])
@app.get(f"{API_PREFIX}/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "message": "ForeSightAI is running!"}


# Include API routes
app.include_router(locations.router, prefix=f"{API_PREFIX}/locations", tags=["Locations"])
app.include_router(hazards.router, prefix=f"{API_PREFIX}/hazards", tags=["Hazards"])
app.include_router(recommendations.router, prefix=f"{API_PREFIX}/recommendations", tags=["Recommendations"])
