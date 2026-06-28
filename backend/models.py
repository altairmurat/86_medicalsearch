import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

def uid():
    return str(uuid.uuid4())

class Clinic(Base):
    __tablename__ = "clinics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200), index=True)
    city: Mapped[str] = mapped_column(String(80), index=True)
    address: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(100), default="")
    working_hours: Mapped[str] = mapped_column(String(120), default="08:00–20:00")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    online_booking: Mapped[bool] = mapped_column(Boolean, default=False)
    latitude: Mapped[float] = mapped_column(Float, default=0)
    longitude: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    prices = relationship("Price", back_populates="clinic", cascade="all, delete-orphan")

class Service(Base):
    __tablename__ = "services"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(220), index=True, unique=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    synonyms: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    prices = relationship("Price", back_populates="service")

class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("clinic_id", "service_id", name="uq_clinic_service"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    clinic_id: Mapped[str] = mapped_column(String(36), ForeignKey("clinics.id"), index=True)
    service_id: Mapped[str] = mapped_column(String(36), ForeignKey("services.id"), index=True)
    service_name_raw: Mapped[str] = mapped_column(String(255))
    price_kzt: Mapped[int] = mapped_column(Integer, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="KZT")
    duration_days: Mapped[int] = mapped_column(Integer, default=1)
    parsed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    clinic = relationship("Clinic", back_populates="prices")
    service = relationship("Service", back_populates="prices")

class ParserLog(Base):
    __tablename__ = "parser_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_name: Mapped[str] = mapped_column(String(120))
    source_url: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class RawRecord(Base):
    __tablename__ = "raw_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_url: Mapped[str] = mapped_column(String(500))
    raw_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
