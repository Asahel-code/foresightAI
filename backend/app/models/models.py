from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    admin_level = Column(Integer, default=0)  # 0: country, 1: region, 2: county
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom_wkt = Column(Text, nullable=False)  # WKT representation for complex boundaries
    country_code = Column(String, nullable=False, default="KE")  # default to Kenya (KE) or any chosen country

    parent = relationship("Location", remote_side=[id], backref="children")
    observations = relationship("HazardObservation", back_populates="location")
    assets = relationship("ExposureAsset", back_populates="location")
    vulnerabilities = relationship("VulnerabilityIndicator", back_populates="location")
    recommendations = relationship("Recommendation", back_populates="location")
    # NOTE: EarlyAction is a global catalog (no location_id FK) — no relationship here


class HazardObservation(Base):
    __tablename__ = "hazard_observations"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    hazard_type = Column(String, default="flood", nullable=False)
    observation_date = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)  # mm, m, etc.
    source = Column(String, nullable=False)  # CHIRPS, sensor, etc.
    status = Column(String, default="normal", nullable=False)  # normal, warning, critical

    location = relationship("Location", back_populates="observations")


class ExposureAsset(Base):
    __tablename__ = "exposure_assets"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    asset_name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # bridge, hospital, school, cropland, settlement
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    population = Column(Integer, default=0)
    value_usd = Column(Float, default=0.0)

    location = relationship("Location", back_populates="assets")


class VulnerabilityIndicator(Base):
    __tablename__ = "vulnerability_indicators"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    indicator_name = Column(String, nullable=False)  # poverty_index, age_dependency, access_to_water, etc.
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)

    location = relationship("Location", back_populates="vulnerabilities")


class EarlyAction(Base):
    __tablename__ = "early_actions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    hazard_type = Column(String, default="flood")
    # Add fields for lead time, cost, target population etc. as needed
    # For MVP, keeping it simple

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    hazard_level = Column(String, nullable=False)  # low, medium, high
    recommendation_text = Column(Text, nullable=False)
    reasoning_chain = Column(Text, nullable=False)  # JSON or text tracing the graph evidence
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    location = relationship("Location", back_populates="recommendations")
