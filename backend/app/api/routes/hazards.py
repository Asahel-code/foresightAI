from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models import models, schemas

router = APIRouter()


@router.get("/{location_id}", response_model=List[schemas.HazardObservationOut])
def get_hazards_for_location(location_id: int, db: Session = Depends(get_db)):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return db.query(models.HazardObservation).filter(models.HazardObservation.location_id == location_id).all()


@router.post("/", response_model=schemas.HazardObservationOut)
def create_hazard_observation(obs: schemas.HazardObservationCreate, db: Session = Depends(get_db)):
    # Check if location exists
    location = db.query(models.Location).filter(models.Location.id == obs.location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    db_obs = models.HazardObservation(
        location_id=obs.location_id,
        hazard_type=obs.hazard_type,
        observation_date=obs.observation_date,
        value=obs.value,
        unit=obs.unit,
        source=obs.source,
        status=obs.status
    )
    db.add(db_obs)
    db.commit()
    db.refresh(db_obs)
    return db_obs
