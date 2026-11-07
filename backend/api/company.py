"""API routes for company profile management."""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, Base, engine
import models
import schemas

router = APIRouter(prefix="/company", tags=["Company Profile"])


def _ensure_company(db: Session) -> models.Company:
    """Ensure a singleton company record exists (NEXORA AI baseline)."""
    company = db.query(models.Company).first()
    if not company:
        company = models.Company(
            name="NEXORA AI",
            description="",
            website="",
            contact_email="",
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


@router.get("/", response_model=schemas.CompanyOut)
def get_company(db: Session = Depends(get_db)):
    """Get the company record (NEXORA AI)."""
    company = _ensure_company(db)
    return company


@router.patch("/", response_model=schemas.CompanyOut)
def update_company(update: schemas.CompanyUpdate, db: Session = Depends(get_db)):
    """Update top-level company fields."""
    company = _ensure_company(db)
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company


@router.get("/sections", response_model=List[schemas.CompanySectionOut])
def list_sections(db: Session = Depends(get_db)):
    """List all company profile sections."""
    company = _ensure_company(db)
    return company.sections


@router.get("/sections/{section_id}", response_model=schemas.CompanySectionOut)
def get_section(section_id: str, db: Session = Depends(get_db)):
    """Get a single company profile section."""
    company = _ensure_company(db)
    section = (
        db.query(models.CompanySection)
        .filter_by(company_id=company.id, section_id=section_id)
        .first()
    )
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_id}' not found")
    return section


@router.put("/sections/{section_id}", response_model=schemas.CompanySectionOut)
def save_section(
    section_id: str,
    payload: schemas.CompanySectionCreate,
    db: Session = Depends(get_db),
):
    """Create or replace a company profile section (add/edit/save entries)."""
    company = _ensure_company(db)
    section = (
        db.query(models.CompanySection)
        .filter_by(company_id=company.id, section_id=section_id)
        .first()
    )
    if section:
        section.title = payload.title
        section.data = payload.data
        section.is_sample = payload.is_sample
    else:
        section = models.CompanySection(
            company_id=company.id,
            section_id=section_id,
            title=payload.title,
            data=payload.data,
            is_sample=payload.is_sample,
        )
        db.add(section)
    db.commit()
    db.refresh(section)
    return section


@router.patch("/sections/{section_id}", response_model=schemas.CompanySectionOut)
def patch_section(
    section_id: str,
    payload: schemas.CompanySectionUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a company profile section."""
    company = _ensure_company(db)
    section = (
        db.query(models.CompanySection)
        .filter_by(company_id=company.id, section_id=section_id)
        .first()
    )
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_id}' not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(section, field, value)
    db.commit()
    db.refresh(section)
    return section


@router.delete("/sections/{section_id}")
def delete_section(section_id: str, db: Session = Depends(get_db)):
    """Delete a company profile section."""
    company = _ensure_company(db)
    section = (
        db.query(models.CompanySection)
        .filter_by(company_id=company.id, section_id=section_id)
        .first()
    )
    if not section:
        raise HTTPException(status_code=404, detail=f"Section '{section_id}' not found")
    db.delete(section)
    db.commit()
    return {"ok": True, "message": f"Section '{section_id}' deleted"}


@router.get("/profile", response_model=schemas.CompanyProfileOut)
def get_full_profile(db: Session = Depends(get_db)):
    """Get the full company profile with completeness calculation."""
    company = _ensure_company(db)
    sections = company.sections
    section_list = [schemas.CompanySectionOut.model_validate(s) for s in sections]

    # Calculate completion: fraction of sections that have at least some data
    total = len(sections) or 1
    filled = sum(1 for s in sections if s.data and any(str(v).strip() for v in s.data.values()))
    overall = round((filled / total) * 100)

    return schemas.CompanyProfileOut(
        id=company.id,
        name=company.name,
        description=company.description,
        website=company.website,
        contact_email=company.contact_email,
        sections=section_list,
        completeness={"overall": overall, "sections_total": total, "sections_filled": filled},
    )
