from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


# Location Schemas
class LocationBase(BaseModel):
    name: str
    admin_level: int = 0
    parent_id: Optional[int] = None
    latitude: float
    longitude: float
    geom_wkt: Optional[str] = None
    country_code: str = "KE"


class LocationCreate(LocationBase):
    pass


class LocationOut(LocationBase):
    id: int

    class Config:
        from_attributes = True


# HazardObservation Schemas
class HazardObservationBase(BaseModel):
    location_id: int
    hazard_type: str = "flood"
    observation_date: datetime
    value: float
    unit: str
    source: str
    status: str = "normal"


class HazardObservationCreate(HazardObservationBase):
    pass


class HazardObservationOut(HazardObservationBase):
    id: int

    class Config:
        from_attributes = True


# ExposureAsset Schemas
class ExposureAssetBase(BaseModel):
    location_id: int
    asset_name: str
    asset_type: str
    latitude: float
    longitude: float
    population: int = 0
    value_usd: float = 0.0


class ExposureAssetCreate(ExposureAssetBase):
    pass


class ExposureAssetOut(ExposureAssetBase):
    id: int

    class Config:
        from_attributes = True


# VulnerabilityIndicator Schemas
class VulnerabilityIndicatorBase(BaseModel):
    location_id: int
    indicator_name: str
    value: float
    unit: str


class VulnerabilityIndicatorCreate(VulnerabilityIndicatorBase):
    pass


class VulnerabilityIndicatorOut(VulnerabilityIndicatorBase):
    id: int

    class Config:
        from_attributes = True


# Recommendation Schemas
class RecommendationRequest(BaseModel):
    location_id: int
    hazard_type: str = "flood"


class RecommendationBase(BaseModel):
    location_id: int
    hazard_level: str
    recommendation_text: str
    reasoning_chain: str


class RecommendationCreate(RecommendationBase):
    pass


class RecommendationOut(RecommendationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Full Location Detail with Exposure, Vulnerability, and Hazards
class EarlyActionBase(BaseModel):
    name: str
    description: str
    hazard_type: str = "flood"

class EarlyActionCreate(EarlyActionBase):
    pass

class EarlyActionOut(EarlyActionBase):
    id: int

    class Config:
        from_attributes = True

# Full Location Detail with Exposure, Vulnerability, Hazards, and Recommendations
class LocationDetailOut(LocationOut):
    observations: List[HazardObservationOut] = []
    assets: List[ExposureAssetOut] = []
    vulnerabilities: List[VulnerabilityIndicatorOut] = []
    recommendations: List[RecommendationOut] = []
    # Note: EarlyAction is a global catalog — fetched separately via /early-actions endpoint

    class Config:
        from_attributes = True
