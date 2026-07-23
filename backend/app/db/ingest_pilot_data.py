"""
ForeSightAI — Pilot Data Ingestion Script
==========================================
Step 4: Ingest Pilot Data

Populates the PostgreSQL database with a meaningful baseline dataset for
the Kenya / Tana River County flood early warning pilot.

Data categories covered (per System_structure.md Step 4):
  1. Country and admin boundaries
  2. River and floodplain data (as exposure assets + observations)
  3. Population and vulnerability layers
  4. Weather and forecast observations
  5. Infrastructure and critical facility data

This script is fully idempotent — safe to run multiple times without
creating duplicate records.

Usage (from project root, with backend venv active):
    python backend/app/db/ingest_pilot_data.py
"""

import sys
import os
from datetime import datetime, timedelta, UTC

# ---------------------------------------------------------------------------
# Path setup
# In the Docker container: WORKDIR=/app, backend/ contents copied to /app/
#   => this script lives at /app/app/db/ingest_pilot_data.py
#   => go up two levels (../../) to reach /app, which contains the 'app' package
# Locally (running from foresightAI/backend/): same two-level logic works.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.session import SessionLocal, Base, engine
from app.models import models


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_or_create_location(db, *, name, admin_level, parent_id, latitude, longitude,
                           geom_wkt, country_code="KE"):
    """Return existing location or create a new one."""
    loc = db.query(models.Location).filter(models.Location.name == name).first()
    if not loc:
        loc = models.Location(
            name=name,
            admin_level=admin_level,
            parent_id=parent_id,
            latitude=latitude,
            longitude=longitude,
            geom_wkt=geom_wkt,
            country_code=country_code,
        )
        db.add(loc)
        db.flush()   # get generated ID without full commit
        print(f"  [+] Location: {name}  (admin_level={admin_level}, id={loc.id})")
    else:
        print(f"  [=] Location already exists: {name}  (id={loc.id})")
    return loc


def get_or_create_asset(db, *, location_id, asset_name, asset_type,
                        latitude, longitude, population=0, value_usd=0.0):
    asset = db.query(models.ExposureAsset).filter(
        models.ExposureAsset.asset_name == asset_name,
        models.ExposureAsset.location_id == location_id,
    ).first()
    if not asset:
        asset = models.ExposureAsset(
            location_id=location_id,
            asset_name=asset_name,
            asset_type=asset_type,
            latitude=latitude,
            longitude=longitude,
            population=population,
            value_usd=value_usd,
        )
        db.add(asset)
        print(f"  [+] Asset: {asset_name} ({asset_type})")
    else:
        print(f"  [=] Asset already exists: {asset_name}")
    return asset


def get_or_create_vulnerability(db, *, location_id, indicator_name, value, unit):
    ind = db.query(models.VulnerabilityIndicator).filter(
        models.VulnerabilityIndicator.indicator_name == indicator_name,
        models.VulnerabilityIndicator.location_id == location_id,
    ).first()
    if not ind:
        ind = models.VulnerabilityIndicator(
            location_id=location_id,
            indicator_name=indicator_name,
            value=value,
            unit=unit,
        )
        db.add(ind)
        print(f"  [+] Vulnerability indicator: {indicator_name} = {value} {unit}")
    else:
        print(f"  [=] Vulnerability indicator already exists: {indicator_name}")
    return ind


def get_or_create_observation(db, *, location_id, hazard_type, observation_date,
                              value, unit, source, status):
    obs = db.query(models.HazardObservation).filter(
        models.HazardObservation.location_id == location_id,
        models.HazardObservation.source == source,
        models.HazardObservation.hazard_type == hazard_type,
        models.HazardObservation.observation_date == observation_date,
    ).first()
    if not obs:
        obs = models.HazardObservation(
            location_id=location_id,
            hazard_type=hazard_type,
            observation_date=observation_date,
            value=value,
            unit=unit,
            source=source,
            status=status,
        )
        db.add(obs)
        print(f"  [+] Observation: {hazard_type} {value} {unit} [{status}] @ {source}")
    else:
        print(f"  [=] Observation already exists: {source} {observation_date}")
    return obs


def get_or_create_early_action(db, *, name, description, hazard_type):
    action = db.query(models.EarlyAction).filter(models.EarlyAction.name == name).first()
    if not action:
        action = models.EarlyAction(
            name=name,
            description=description,
            hazard_type=hazard_type,
        )
        db.add(action)
        print(f"  [+] Early action: {name}")
    else:
        print(f"  [=] Early action already exists: {name}")
    return action


# ===========================================================================
# Main ingestion routine
# ===========================================================================

def ingest_pilot_data():
    # Ensure tables exist (safe if already created)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now = datetime.now(UTC).replace(microsecond=0)

        # -------------------------------------------------------------------
        # 1. ADMIN BOUNDARIES
        #    Kenya (country) → Tana River County (county) → 3 sub-counties
        # -------------------------------------------------------------------
        print("\n── 1. Admin Boundaries ──")

        kenya = get_or_create_location(
            db,
            name="Kenya",
            admin_level=0,
            parent_id=None,
            latitude=-1.2921,
            longitude=36.8219,
            country_code="KE",
            geom_wkt=(
                "POLYGON((34.0 -4.67, 41.9 -4.67, 41.9 4.62, 34.0 4.62, 34.0 -4.67))"
            ),
        )

        uganda = get_or_create_location(
            db,
            name="Uganda",
            admin_level=0,
            parent_id=None,
            latitude=1.3733,
            longitude=32.2903,
            country_code="UG",
            geom_wkt=(
                "POLYGON((29.5 -1.5, 35.0 -1.5, 35.0 4.2, 29.5 4.2, 29.5 -1.5))"
            ),
        )

        tana_river = get_or_create_location(
            db,
            name="Tana River County",
            admin_level=1,
            parent_id=kenya.id,
            latitude=-1.5222,
            longitude=40.0336,
            country_code="KE",
            geom_wkt=(
                "POLYGON((38.5 -2.5, 40.8 -2.5, 40.8 -0.5, 38.5 -0.5, 38.5 -2.5))"
            ),
        )

        # Sub-counties (admin_level=2)
        bura = get_or_create_location(
            db,
            name="Bura Sub-County",
            admin_level=2,
            parent_id=tana_river.id,
            latitude=-1.135,
            longitude=39.943,
            country_code="KE",
            geom_wkt=(
                "POLYGON((39.6 -1.4, 40.2 -1.4, 40.2 -0.9, 39.6 -0.9, 39.6 -1.4))"
            ),
        )

        garsen = get_or_create_location(
            db,
            name="Garsen Sub-County",
            admin_level=2,
            parent_id=tana_river.id,
            latitude=-2.2764,
            longitude=40.1203,
            country_code="KE",
            geom_wkt=(
                "POLYGON((39.8 -2.5, 40.6 -2.5, 40.6 -1.8, 39.8 -1.8, 39.8 -2.5))"
            ),
        )

        galole = get_or_create_location(
            db,
            name="Galole Sub-County",
            admin_level=2,
            parent_id=tana_river.id,
            latitude=-1.4858,
            longitude=40.0336,
            country_code="KE",
            geom_wkt=(
                "POLYGON((39.5 -1.9, 40.5 -1.9, 40.5 -1.3, 39.5 -1.3, 39.5 -1.9))"
            ),
        )

        kampala = get_or_create_location(
            db,
            name="Kampala District",
            admin_level=1,
            parent_id=uganda.id,
            latitude=0.3476,
            longitude=32.5825,
            country_code="UG",
            geom_wkt=(
                "POLYGON((32.50 0.20, 32.75 0.20, 32.75 0.45, 32.50 0.45, 32.50 0.20))"
            ),
        )

        nakawa = get_or_create_location(
            db,
            name="Nakawa Division",
            admin_level=2,
            parent_id=kampala.id,
            latitude=0.3298,
            longitude=32.6060,
            country_code="UG",
            geom_wkt=(
                "POLYGON((32.58 0.31, 32.64 0.31, 32.64 0.36, 32.58 0.36, 32.58 0.31))"
            ),
        )

        db.commit()

        # -------------------------------------------------------------------
        # 2. INFRASTRUCTURE AND CRITICAL FACILITY DATA
        #    Bridges, hospitals, schools, cropland, river gauging stations
        # -------------------------------------------------------------------
        print("\n── 2. Infrastructure & Critical Facility Data ──")

        # Tana River County level assets
        get_or_create_asset(db, location_id=tana_river.id,
            asset_name="Tana River Bridge (Hola)",
            asset_type="bridge",
            latitude=-1.510, longitude=40.028,
            population=0, value_usd=15_000_000.0)

        get_or_create_asset(db, location_id=tana_river.id,
            asset_name="Hola District Hospital",
            asset_type="hospital",
            latitude=-1.502, longitude=40.021,
            population=1200, value_usd=5_000_000.0)

        get_or_create_asset(db, location_id=tana_river.id,
            asset_name="Hola Town Water Treatment Plant",
            asset_type="water_facility",
            latitude=-1.507, longitude=40.025,
            population=12_000, value_usd=3_200_000.0)

        # Bura sub-county assets
        get_or_create_asset(db, location_id=bura.id,
            asset_name="Bura Irrigation Scheme",
            asset_type="cropland",
            latitude=-1.135, longitude=39.852,
            population=4500, value_usd=8_500_000.0)

        get_or_create_asset(db, location_id=bura.id,
            asset_name="Bura Primary Health Centre",
            asset_type="hospital",
            latitude=-1.109, longitude=39.934,
            population=500, value_usd=800_000.0)

        get_or_create_asset(db, location_id=bura.id,
            asset_name="Bura Girls Secondary School",
            asset_type="school",
            latitude=-1.128, longitude=39.941,
            population=320, value_usd=420_000.0)

        # Garsen sub-county assets
        get_or_create_asset(db, location_id=garsen.id,
            asset_name="Garsen Bridge",
            asset_type="bridge",
            latitude=-2.277, longitude=40.117,
            population=0, value_usd=9_000_000.0)

        get_or_create_asset(db, location_id=garsen.id,
            asset_name="Garsen Town Settlement",
            asset_type="settlement",
            latitude=-2.280, longitude=40.122,
            population=22_000, value_usd=0.0)

        get_or_create_asset(db, location_id=garsen.id,
            asset_name="Tana Delta Mangrove Floodplain",
            asset_type="floodplain",
            latitude=-2.450, longitude=40.250,
            population=3400, value_usd=2_100_000.0)

        # Galole sub-county assets
        get_or_create_asset(db, location_id=galole.id,
            asset_name="Garissa Primary School",
            asset_type="school",
            latitude=-0.453, longitude=39.641,
            population=650, value_usd=350_000.0)

        # Uganda assets
        get_or_create_asset(db, location_id=kampala.id,
            asset_name="Kampala Central Floodgate",
            asset_type="floodgate",
            latitude=0.3476, longitude=32.5825,
            population=0, value_usd=2_100_000.0)

        get_or_create_asset(db, location_id=nakawa.id,
            asset_name="Nakawa Community Clinic",
            asset_type="hospital",
            latitude=0.3298, longitude=32.6060,
            population=900, value_usd=1_100_000.0)

        db.commit()

        # -------------------------------------------------------------------
        # 3. RIVER AND FLOODPLAIN DATA
        #    River gauging stations modelled as exposure assets with type
        #    "river_gauge" — they generate the observations below
        # -------------------------------------------------------------------
        print("\n── 3. River & Floodplain Data ──")

        gauge_hola = get_or_create_asset(db, location_id=tana_river.id,
            asset_name="Tana River Gauge — Hola",
            asset_type="river_gauge",
            latitude=-1.508, longitude=40.030,
            population=0, value_usd=0.0)

        gauge_bura = get_or_create_asset(db, location_id=bura.id,
            asset_name="Tana River Gauge — Bura",
            asset_type="river_gauge",
            latitude=-1.138, longitude=39.950,
            population=0, value_usd=0.0)

        gauge_garsen = get_or_create_asset(db, location_id=garsen.id,
            asset_name="Tana River Gauge — Garsen",
            asset_type="river_gauge",
            latitude=-2.281, longitude=40.119,
            population=0, value_usd=0.0)

        db.commit()

        # -------------------------------------------------------------------
        # 4. POPULATION AND VULNERABILITY LAYERS
        #    Socio-economic indicators per location
        # -------------------------------------------------------------------
        print("\n── 4. Population & Vulnerability Layers ──")

        # Tana River County (county-level aggregate)
        for ind in [
            ("Poverty Index",              0.62,  "ratio",   tana_river.id),
            ("Age Dependency Ratio",        0.85,  "ratio",   tana_river.id),
            ("Flood Susceptibility Index",  0.78,  "index",   tana_river.id),
            ("Access to Safe Water",        0.35,  "ratio",   tana_river.id),
            ("Population Density",         18.3,   "persons/km2", tana_river.id),
            ("Female-Headed Households",    0.42,  "ratio",   tana_river.id),
            ("Households with Disability",  0.11,  "ratio",   tana_river.id),
        ]:
            get_or_create_vulnerability(db, location_id=ind[3],
                indicator_name=ind[0], value=ind[1], unit=ind[2])

        # Bura sub-county
        for ind in [
            ("Poverty Index",              0.58,  "ratio"),
            ("Flood Susceptibility Index",  0.82,  "index"),
            ("Access to Safe Water",        0.28,  "ratio"),
            ("Population Density",          9.6,   "persons/km2"),
        ]:
            get_or_create_vulnerability(db, location_id=bura.id,
                indicator_name=ind[0], value=ind[1], unit=ind[2])

        # Garsen sub-county (delta area — highest flood risk)
        for ind in [
            ("Poverty Index",              0.71,  "ratio"),
            ("Flood Susceptibility Index",  0.91,  "index"),
            ("Access to Safe Water",        0.22,  "ratio"),
            ("Coastal Inundation Risk",     0.76,  "index"),
            ("Population Density",         24.1,   "persons/km2"),
        ]:
            get_or_create_vulnerability(db, location_id=garsen.id,
                indicator_name=ind[0], value=ind[1], unit=ind[2])

        # Galole sub-county
        for ind in [
            ("Poverty Index",              0.65,  "ratio"),
            ("Flood Susceptibility Index",  0.74,  "index"),
            ("Access to Safe Water",        0.38,  "ratio"),
        ]:
            get_or_create_vulnerability(db, location_id=galole.id,
                indicator_name=ind[0], value=ind[1], unit=ind[2])

        # Kampala district (Uganda)
        for ind in [
            ("Poverty Index",              0.41,  "ratio"),
            ("Flood Susceptibility Index",  0.69,  "index"),
            ("Access to Safe Water",        0.62,  "ratio"),
        ]:
            get_or_create_vulnerability(db, location_id=kampala.id,
                indicator_name=ind[0], value=ind[1], unit=ind[2])

        db.commit()

        # -------------------------------------------------------------------
        # 5. WEATHER AND FORECAST OBSERVATIONS
        #    River gauge readings + CHIRPS rainfall + GloFAS river discharge
        #    Simulates a developing flood event over a 48-hour window
        # -------------------------------------------------------------------
        print("\n── 5. Weather & Forecast Observations ──")

        # -- Hola river gauge (Tana River County) — rising flood scenario --
        gauge_readings_hola = [
            (now - timedelta(hours=48), 3.9,  "meters", "river_gauge_hola", "normal"),
            (now - timedelta(hours=36), 4.2,  "meters", "river_gauge_hola", "normal"),
            (now - timedelta(hours=24), 5.1,  "meters", "river_gauge_hola", "warning"),
            (now - timedelta(hours=12), 5.8,  "meters", "river_gauge_hola", "warning"),
            (now - timedelta(hours=6),  6.3,  "meters", "river_gauge_hola", "critical"),
            (now,                       6.7,  "meters", "river_gauge_hola", "critical"),
        ]
        for obs_date, val, unit, src, status in gauge_readings_hola:
            get_or_create_observation(db, location_id=tana_river.id,
                hazard_type="flood", observation_date=obs_date,
                value=val, unit=unit, source=src, status=status)

        # -- Bura river gauge --
        gauge_readings_bura = [
            (now - timedelta(hours=24), 3.1,  "meters", "river_gauge_bura", "normal"),
            (now - timedelta(hours=12), 4.0,  "meters", "river_gauge_bura", "warning"),
            (now,                       4.9,  "meters", "river_gauge_bura", "warning"),
        ]
        for obs_date, val, unit, src, status in gauge_readings_bura:
            get_or_create_observation(db, location_id=bura.id,
                hazard_type="flood", observation_date=obs_date,
                value=val, unit=unit, source=src, status=status)

        # -- Garsen river gauge (delta — critical) --
        gauge_readings_garsen = [
            (now - timedelta(hours=24), 5.5,  "meters", "river_gauge_garsen", "warning"),
            (now - timedelta(hours=12), 6.8,  "meters", "river_gauge_garsen", "critical"),
            (now,                       7.2,  "meters", "river_gauge_garsen", "critical"),
        ]
        for obs_date, val, unit, src, status in gauge_readings_garsen:
            get_or_create_observation(db, location_id=garsen.id,
                hazard_type="flood", observation_date=obs_date,
                value=val, unit=unit, source=src, status=status)

        # -- CHIRPS rainfall (county-level) --
        chirps_readings = [
            (now - timedelta(hours=48), 18.3, "mm/day", "CHIRPS", "normal"),
            (now - timedelta(hours=24), 38.7, "mm/day", "CHIRPS", "warning"),
            (now,                       42.5, "mm/day", "CHIRPS", "warning"),
        ]
        for obs_date, val, unit, src, status in chirps_readings:
            get_or_create_observation(db, location_id=tana_river.id,
                hazard_type="rainfall", observation_date=obs_date,
                value=val, unit=unit, source=src, status=status)

        # -- GloFAS 5-day river discharge forecast (county-level) --
        glofas_forecast = [
            (now + timedelta(hours=24),  820.0, "m3/s", "GloFAS_forecast", "warning"),
            (now + timedelta(hours=48), 1050.0, "m3/s", "GloFAS_forecast", "critical"),
            (now + timedelta(hours=72), 1180.0, "m3/s", "GloFAS_forecast", "critical"),
            (now + timedelta(hours=96),  970.0, "m3/s", "GloFAS_forecast", "warning"),
            (now + timedelta(hours=120), 710.0, "m3/s", "GloFAS_forecast", "normal"),
        ]
        for obs_date, val, unit, src, status in glofas_forecast:
            get_or_create_observation(db, location_id=tana_river.id,
                hazard_type="river_discharge", observation_date=obs_date,
                value=val, unit=unit, source=src, status=status)

        # -- ECMWF temperature and wind (Tana River County) --
        get_or_create_observation(db, location_id=tana_river.id,
            hazard_type="temperature",
            observation_date=now,
            value=34.2, unit="°C",
            source="ECMWF", status="normal")

        # -- Uganda rainfall and flood observations (Kampala) --
        get_or_create_observation(db, location_id=kampala.id,
            hazard_type="flood",
            observation_date=now,
            value=1.8, unit="meters",
            source="UG-forecast", status="warning")

        get_or_create_observation(db, location_id=nakawa.id,
            hazard_type="rainfall",
            observation_date=now,
            value=41.2, unit="mm/day",
            source="UG-rainfall", status="warning")

        db.commit()

        # -------------------------------------------------------------------
        # 6. EARLY ACTIONS CATALOG
        # -------------------------------------------------------------------
        print("\n── 6. Early Actions Catalog ──")

        early_actions = [
            (
                "Issue Flood Early Warning Alert",
                "Broadcast a flood early warning alert to communities in Tana River County "
                "via SMS, radio, and community leaders. Include safe evacuation routes.",
                "flood",
            ),
            (
                "Activate Emergency Evacuation Plan",
                "Initiate the county emergency evacuation plan for high-risk zones along the "
                "Tana River. Prioritise Garsen and Hola riverine settlements.",
                "flood",
            ),
            (
                "Pre-position Emergency Relief Supplies",
                "Pre-position food, clean water, and non-food items at Hola district emergency "
                "warehouse and identified evacuation centers.",
                "flood",
            ),
            (
                "Activate Emergency Shelters",
                "Open and staff designated emergency shelters (schools, community halls) for "
                "displaced populations in Bura, Galole, and Garsen sub-counties.",
                "flood",
            ),
            (
                "Distribute Sandbags to Critical Infrastructure",
                "Deliver sandbags to protect Hola District Hospital, Garsen Bridge, and the "
                "Bura Irrigation Scheme pump stations from floodwater ingress.",
                "flood",
            ),
            (
                "Suspend School Operations in Flood Zones",
                "Temporarily close schools in identified flood-risk zones and reassign "
                "facilities as emergency shelters where appropriate.",
                "flood",
            ),
            (
                "Deploy Water Quality Monitoring Teams",
                "Deploy rapid water quality testing teams to monitor drinking water sources "
                "for contamination during and after flood events.",
                "flood",
            ),
            (
                "Alert Health Facilities for Surge Capacity",
                "Notify Hola District Hospital and sub-county health centres to prepare for "
                "increased patient load (injuries, waterborne disease) during the flood.",
                "flood",
            ),
            (
                "Activate Kampala Drainage Response",
                "Deploy rapid drainage clearance teams in Nakawa Division and prioritize low-lying communities near the city drainage channels.",
                "flood",
            ),
        ]

        for name, description, hazard_type in early_actions:
            get_or_create_early_action(db, name=name, description=description,
                                       hazard_type=hazard_type)

        db.commit()

        print("\n✓ Pilot data ingestion completed successfully!")
        print(f"  Pilot geography : Kenya → Tana River County (+ Bura, Garsen, Galole)")
        print(f"  Hazard          : Flood")
        print(f"  Observations    : {len(gauge_readings_hola) + len(gauge_readings_bura) + len(gauge_readings_garsen) + len(chirps_readings) + len(glofas_forecast) + 1} total")
        print(f"  Early actions   : {len(early_actions)}")

    except Exception as exc:
        db.rollback()
        print(f"\n✗ Error during ingestion: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ingest_pilot_data()
