from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal, get_db
from models import Clinic, Service, Price, ParserLog, RawRecord
from normalizer import normalize_query, suggestions
from seed import seed_if_empty, refresh_standard_sources
from ai import ask_ai


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="MedServicePrice.kz API",
    version="5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    message: str


def ensure_seeded(db: Session) -> None:
    """
    База заполняется не на startup, а при первом запросе.
    Это нужно, чтобы Render успевал открыть порт.
    """
    if db.query(Price).count() == 0:
        seed_if_empty(db)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    ensure_seeded(db)

    return {
        "clinics": db.query(Clinic).count(),
        "services": db.query(Service).count(),
        "prices": db.query(Price).count(),
        "cities": db.query(Clinic.city).distinct().count(),
    }


@app.post("/api/refresh")
def refresh(db: Session = Depends(get_db)):
    return refresh_standard_sources(db)


@app.get("/api/filters")
def filters(db: Session = Depends(get_db)):
    ensure_seeded(db)

    return {
        "cities": [
            x[0]
            for x in db.query(Clinic.city)
            .distinct()
            .order_by(Clinic.city)
            .all()
        ],
        "categories": [
            x[0]
            for x in db.query(Service.category)
            .distinct()
            .order_by(Service.category)
            .all()
        ],
    }


@app.get("/api/suggest")
def suggest(q: str = ""):
    return {
        "query": q,
        "normalized": normalize_query(q),
        "suggestions": suggestions(q),
    }


@app.get("/api/search")
def search(
    q: str = "",
    city: str = "",
    category: str = "",
    min_price: int = 0,
    max_price: int = 1000000,
    sort: str = "price_asc",
    limit: int = 1200,
    db: Session = Depends(get_db),
):
    ensure_seeded(db)

    normalized = normalize_query(q)

    query = (
        db.query(Price, Clinic, Service)
        .join(Clinic)
        .join(Service)
        .filter(Price.is_active == True)
    )

    if q:
        query = query.filter(
            or_(
                Service.name.ilike(f"%{normalized}%"),
                Service.synonyms.ilike(f"%{q}%"),
                Price.service_name_raw.ilike(f"%{q}%"),
            )
        )

    if city:
        query = query.filter(Clinic.city == city)

    if category:
        query = query.filter(Service.category == category)

    query = query.filter(
        Price.price_kzt >= min_price,
        Price.price_kzt <= max_price,
    )

    if sort == "price_desc":
        query = query.order_by(Price.price_kzt.desc())
    elif sort == "rating":
        query = query.order_by(Clinic.rating.desc(), Price.price_kzt.asc())
    else:
        query = query.order_by(Price.price_kzt.asc())

    results = []

    for price, clinic, service in query.limit(min(limit, 5000)).all():
        results.append(
            {
                "clinic_id": clinic.id,
                "clinic_name": clinic.name,
                "city": clinic.city,
                "address": clinic.address,
                "phone": clinic.phone,
                "working_hours": clinic.working_hours,
                "source_url": clinic.source_url,
                "rating": clinic.rating,
                "online_booking": clinic.online_booking,
                "lat": clinic.latitude,
                "lon": clinic.longitude,
                "service": service.name,
                "category": service.category,
                "raw_name": price.service_name_raw,
                "price_kzt": price.price_kzt,
                "duration_days": price.duration_days,
                "parsed_at": price.parsed_at.isoformat(),
            }
        )

    return {
        "query": q,
        "normalized": normalized,
        "count": len(results),
        "results": results,
    }


@app.get("/api/services")
def services(db: Session = Depends(get_db)):
    ensure_seeded(db)

    rows = db.query(Service).order_by(Service.category, Service.name).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "synonyms": s.synonyms,
        }
        for s in rows
    ]


@app.get("/api/clinics")
def clinics(db: Session = Depends(get_db)):
    ensure_seeded(db)

    rows = db.query(Clinic).order_by(Clinic.name).all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "city": c.city,
            "address": c.address,
            "lat": c.latitude,
            "lon": c.longitude,
            "rating": c.rating,
            "source_url": c.source_url,
        }
        for c in rows
    ]


@app.post("/api/ai/recommend")
def ai_recommend(data: ChatIn):
    return ask_ai(data.message)


@app.get("/api/logs")
def logs(db: Session = Depends(get_db)):
    items = (
        db.query(ParserLog)
        .order_by(ParserLog.created_at.desc())
        .limit(25)
        .all()
    )

    return [
        {
            "source_name": x.source_name,
            "source_url": x.source_url,
            "status": x.status,
            "message": x.message,
            "created_at": x.created_at.isoformat(),
        }
        for x in items
    ]


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"

if (FRONTEND_DIR / "assets").exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIR / "assets")),
        name="assets",
    )


@app.get("/")
def index():
    index_path = FRONTEND_DIR / "index.html"

    if index_path.exists():
        return FileResponse(str(index_path))

    return JSONResponse(
        {
            "message": "Frontend folder not found.",
            "api_docs": "/docs",
            "health": "/api/health",
        }
    )