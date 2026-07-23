"""
ForeSightAI — RDF Graph Seeder
==============================
Step 4 deliverable: Serialise pilot data from PostgreSQL into RDF Turtle
so the knowledge-graph/ directory contains a baseline set of triples
ready for the reasoning layer (Step 5).

Generates: knowledge-graph/kenya_pilot.ttl

Usage (from project root, with backend venv active):
    python backend/app/db/seed_rdf_graph.py

Dependencies (already in backend requirements):
    rdflib
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# Ensure the backend package root is importable when the script is executed
# directly from either the repository checkout or the Docker container.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.knowledge_graph_utils import (
    build_data_namespace,
    build_data_uri,
    build_graph_output_path,
    slugify,
)

from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS, OWL, XSD
from app.db.session import SessionLocal, Base, engine
from app.models import models

# ---------------------------------------------------------------------------
# Namespace declarations — mirror the ontology URIs exactly
# ---------------------------------------------------------------------------
GEO  = Namespace("http://www.foresightai.org/ontology/geography#")
HAZ  = Namespace("http://www.foresightai.org/ontology/hazards#")
CORE = Namespace("http://www.foresightai.org/ontology/core#")

# Output path for the Turtle file.
# Inside Docker: WORKDIR=/app, COPY backend/ . -> project root is NOT in container.
# We write to /app/knowledge-graph/ which is a subdirectory inside the container.
# Override with KG_OUTPUT_PATH env var if you want a different location.
_default_output_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-graph")
)


def build_graph(db, region_code: str | None = None) -> Graph:
    g = Graph()

    # Bind prefixes for compact Turtle output
    g.bind("geo", GEO)
    g.bind("haz", HAZ)
    g.bind("core", CORE)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)

    normalized_region = (region_code or "ke").strip().lower()
    all_locations = db.query(models.Location).all()
    locations = [
        loc for loc in all_locations
        if (loc.country_code or "ke").strip().lower() == normalized_region
    ]
    if not locations and normalized_region != "global":
        locations = all_locations
        normalized_region = "global"

    data_namespace = build_data_namespace(normalized_region if normalized_region != "global" else None)
    DATA = Namespace(data_namespace)
    g.bind("data", DATA)

    ontology_uri = URIRef(data_namespace.rstrip("/"))
    g.add((ontology_uri, RDF.type, OWL.Ontology))
    g.add((ontology_uri, OWL.imports, URIRef("http://www.foresightai.org/ontology/core")))
    g.add((ontology_uri, RDFS.label, Literal(f"ForeSightAI {normalized_region.upper()} Dataset", lang="en")))
    g.add((ontology_uri, RDFS.comment, Literal(
        f"RDF instance data for the {normalized_region.upper()} pilot region. Generated from the ForeSightAI PostgreSQL database by seed_rdf_graph.py.",
        lang="en",
    )))

    location_uri_map: dict[int, URIRef] = {}

    for loc in locations:
        slug = slugify(loc.name)
        uri = URIRef(build_data_uri(loc.country_code, f"location_{slug}"))
        location_uri_map[loc.id] = uri

        g.add((uri, RDF.type, GEO.Location))
        g.add((uri, GEO.hasName, Literal(loc.name, datatype=XSD.string)))
        g.add((uri, GEO.hasLatitude, Literal(loc.latitude, datatype=XSD.float)))
        g.add((uri, GEO.hasLongitude, Literal(loc.longitude, datatype=XSD.float)))
        g.add((uri, RDFS.label, Literal(loc.name, lang="en")))
        g.add((uri, CORE["hasAdminLevel"], Literal(loc.admin_level, datatype=XSD.integer)))
        g.add((uri, CORE["hasCountryCode"], Literal(loc.country_code, datatype=XSD.string)))

        if loc.geom_wkt:
            g.add((uri, CORE["hasGeometryWKT"], Literal(loc.geom_wkt, datatype=XSD.string)))

        if loc.parent_id and loc.parent_id in location_uri_map:
            g.add((uri, CORE["isPartOf"], location_uri_map[loc.parent_id]))

    for loc in locations:
        if loc.parent_id and loc.parent_id in location_uri_map:
            child_uri = location_uri_map[loc.id]
            parent_uri = location_uri_map[loc.parent_id]
            g.add((child_uri, CORE["isPartOf"], parent_uri))

    location_ids = {loc.id for loc in locations}
    observations = []
    if location_ids:
        observations = db.query(models.HazardObservation).filter(
            models.HazardObservation.location_id.in_(location_ids)
        ).all()

    for obs in observations:
        location = next((loc for loc in locations if loc.id == obs.location_id), None)
        obs_uri = URIRef(
            build_data_uri(
                location.country_code if location else None,
                f"observation_{obs.id}",
            )
        )
        g.add((obs_uri, RDF.type, HAZ.Observation))
        g.add((obs_uri, HAZ.hasValue, Literal(obs.value, datatype=XSD.float)))
        g.add((obs_uri, HAZ.hasUnit, Literal(obs.unit, datatype=XSD.string)))
        g.add((obs_uri, HAZ.hasTimestamp, Literal(obs.observation_date.isoformat(), datatype=XSD.dateTime)))
        g.add((obs_uri, CORE["hasDataSource"], Literal(obs.source, datatype=XSD.string)))
        g.add((obs_uri, CORE["hasStatus"], Literal(obs.status, datatype=XSD.string)))

        if obs.location_id in location_uri_map:
            g.add((obs_uri, CORE.hasLocation, location_uri_map[obs.location_id]))

        hazard_uri = URIRef(build_data_uri(None, f"hazard_{slugify(obs.hazard_type)}"))
        g.add((hazard_uri, RDF.type, HAZ.Hazard))
        g.add((hazard_uri, HAZ.hasType, Literal(obs.hazard_type, datatype=XSD.string)))
        g.add((hazard_uri, RDFS.label, Literal(obs.hazard_type.replace("_", " ").title(), lang="en")))
        g.add((obs_uri, HAZ.observes, hazard_uri))

    assets = []
    if location_ids:
        assets = db.query(models.ExposureAsset).filter(
            models.ExposureAsset.location_id.in_(location_ids)
        ).all()

    for asset in assets:
        asset_uri = URIRef(build_data_uri(None, f"asset_{asset.id}_{slugify(asset.asset_name)}"))
        g.add((asset_uri, RDF.type, CORE.Exposure))
        g.add((asset_uri, RDFS.label, Literal(asset.asset_name, lang="en")))
        g.add((asset_uri, CORE["hasAssetType"], Literal(asset.asset_type, datatype=XSD.string)))
        g.add((asset_uri, GEO.hasLatitude, Literal(asset.latitude, datatype=XSD.float)))
        g.add((asset_uri, GEO.hasLongitude, Literal(asset.longitude, datatype=XSD.float)))

        if asset.population:
            g.add((asset_uri, CORE.hasAffectedPopulation, Literal(asset.population, datatype=XSD.integer)))
        if asset.value_usd:
            g.add((asset_uri, CORE.hasEstimatedCost, Literal(asset.value_usd, datatype=XSD.float)))

        if asset.location_id in location_uri_map:
            g.add((asset_uri, CORE.hasLocation, location_uri_map[asset.location_id]))

    indicators = []
    if location_ids:
        indicators = db.query(models.VulnerabilityIndicator).filter(
            models.VulnerabilityIndicator.location_id.in_(location_ids)
        ).all()

    for ind in indicators:
        ind_uri = URIRef(build_data_uri(None, f"vulnerability_{ind.id}_{slugify(ind.indicator_name)}"))
        g.add((ind_uri, RDF.type, CORE.Vulnerability))
        g.add((ind_uri, RDFS.label, Literal(ind.indicator_name, lang="en")))
        g.add((ind_uri, CORE["hasIndicatorName"], Literal(ind.indicator_name, datatype=XSD.string)))
        g.add((ind_uri, CORE["hasIndicatorValue"], Literal(ind.value, datatype=XSD.float)))
        g.add((ind_uri, CORE["hasIndicatorUnit"], Literal(ind.unit, datatype=XSD.string)))

        if ind.location_id in location_uri_map:
            g.add((ind_uri, CORE.hasLocation, location_uri_map[ind.location_id]))

    actions = db.query(models.EarlyAction).all()
    for action in actions:
        action_uri = URIRef(build_data_uri(None, f"earlyaction_{action.id}_{slugify(action.name)}"))
        g.add((action_uri, RDF.type, CORE.EarlyAction))
        g.add((action_uri, RDFS.label, Literal(action.name, lang="en")))
        g.add((action_uri, CORE.hasDescription, Literal(action.description, datatype=XSD.string)))

        hazard_uri = URIRef(build_data_uri(None, f"hazard_{slugify(action.hazard_type)}"))
        g.add((action_uri, CORE.mitigates, hazard_uri))

    return g


def seed_rdf_graph():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        locations = db.query(models.Location).all()
        region_codes = {
            (loc.country_code or "ke").strip().lower() for loc in locations
        }
        if not region_codes:
            region_codes = {"ke"}

        output_override = os.environ.get("KG_OUTPUT_PATH")
        region_order = sorted(region_codes)
        region_code = os.environ.get("KG_REGION_CODE", region_order[0]).strip().lower()

        print("Building RDF graph from database...")
        if output_override:
            print(f"  Exporting a single graph to {output_override} for region {region_code}")
            g = build_graph(db, region_code=region_code)
            triple_count = len(g)
            print(f"  Graph contains {triple_count} triples.")
            output_dir = os.path.dirname(output_override) or "."
            os.makedirs(output_dir, exist_ok=True)
            g.serialize(destination=output_override, format="turtle")
            print(f"  Serialised to: {output_override}")
        else:
            for region_code in region_order:
                output_path = build_graph_output_path(region_code, _default_output_dir)
                g = build_graph(db, region_code=region_code)
                triple_count = len(g)
                print(f"  Graph contains {triple_count} triples for {region_code}.")
                output_dir = os.path.dirname(output_path) or "."
                os.makedirs(output_dir, exist_ok=True)
                g.serialize(destination=output_path, format="turtle")
                print(f"  Serialised to: {output_path}")

        print("✓ RDF graph seeding complete.")

    except Exception as exc:
        print(f"✗ Error: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_rdf_graph()
