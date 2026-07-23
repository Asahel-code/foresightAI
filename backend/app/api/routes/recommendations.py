from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models import models, schemas
# We'll import services later as we build them
from app.services.reasoning_service import run_reasoning_and_recommendation

router = APIRouter()


@router.post("/", response_model=schemas.RecommendationOut)
def generate_recommendation(req: schemas.RecommendationRequest, db: Session = Depends(get_db)):
    location = db.query(models.Location).filter(models.Location.id == req.location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Run the reasoning service which integrates standard rules + LLM and writes to DB
    recommendation = run_reasoning_and_recommendation(db, req.location_id, req.hazard_type)
    return recommendation


@router.get("/{location_id}", response_model=List[schemas.RecommendationOut])
def get_recommendations_for_location(location_id: int, db: Session = Depends(get_db)):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return db.query(models.Recommendation).filter(models.Recommendation.location_id == location_id).order_by(models.Recommendation.created_at.desc()).all()
