from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.LocationOut])
def get_locations(db: Session = Depends(get_db)):
    return db.query(models.Location).all()


@router.get("/{location_id}", response_model=schemas.LocationDetailOut)
def get_location_detail(location_id: int, db: Session = Depends(get_db)):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.post("/", response_model=schemas.LocationOut)
def create_location(location: schemas.LocationCreate, db: Session = Depends(get_db)):
    db_location = models.Location(
        name=location.name,
        admin_level=location.admin_level,
        parent_id=location.parent_id,
        latitude=location.latitude,
        longitude=location.longitude,
        geom_wkt=location.geom_wkt,
        country_code=location.country_code
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location
