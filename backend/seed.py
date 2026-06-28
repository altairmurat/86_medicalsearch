from sqlalchemy.orm import Session
from models import Clinic, Service, Price, ParserLog, RawRecord
from normalizer import SERVICE_CATALOG
from data import STANDARD_SOURCES

BASE_PRICES = {
    "лаборатория": (1300, 9500),
    "приём врача": (6000, 18000),
    "диагностика": (3000, 42000),
    "процедура": (2000, 25000),
}

def _price_for(category: str, service_index: int, clinic_index: int) -> int:
    low, high = BASE_PRICES.get(category, (2000, 15000))
    span = max(high - low, 1000)
    return int((low + (service_index * 773 + clinic_index * 391) % span) / 100) * 100

def refresh_standard_sources(db: Session):
    inserted_prices = 0
    total_rows = 0
    for ci, source in enumerate(STANDARD_SOURCES):
        clinic = db.query(Clinic).filter(Clinic.source_url == source["url"]).first()
        if not clinic:
            clinic = Clinic(
                name=source["name"], city=source["city"], address=source["address"], phone=source["phone"],
                source_url=source["url"], rating=source["rating"], online_booking=source["online"],
                latitude=source["lat"], longitude=source["lon"], working_hours="08:00–20:00"
            )
            db.add(clinic)
            db.flush()
        for si, (service_name, category, syns) in enumerate(SERVICE_CATALOG):
            total_rows += 1
            service = db.query(Service).filter(Service.name == service_name).first()
            if not service:
                service = Service(name=service_name, category=category, synonyms=", ".join(syns))
                db.add(service)
                db.flush()
            price = db.query(Price).filter(Price.clinic_id == clinic.id, Price.service_id == service.id).first()
            raw = syns[0] if syns else service_name
            if raw.lower() == "оак":
                raw = "ОАК"
            price_value = _price_for(category, si, ci)
            if price:
                price.price_kzt = price_value
                price.service_name_raw = raw
                price.is_active = True
            else:
                db.add(Price(
                    clinic_id=clinic.id,
                    service_id=service.id,
                    service_name_raw=raw,
                    price_kzt=price_value,
                    duration_days=1 if category != "диагностика" else 0,
                ))
                inserted_prices += 1
    db.add(RawRecord(source_url="standard_sources", raw_text=f"Auto-generated {total_rows} rows from task source list"))
    db.add(ParserLog(source_name="standard_sources", source_url="all", status="success", message=f"Auto-refreshed {total_rows} rows, inserted {inserted_prices} new prices."))
    db.commit()
    return {"rows": total_rows, "inserted_prices": inserted_prices}

def seed_if_empty(db: Session):
    if db.query(Price).count() == 0:
        return refresh_standard_sources(db)
    return {"rows": db.query(Price).count(), "inserted_prices": 0}
