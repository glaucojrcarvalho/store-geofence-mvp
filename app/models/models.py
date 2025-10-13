# app/models/models.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geography
from app.core.db import Base

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    geofence_radius_m: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Store(Base):
    __tablename__ = "stores"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address_lines: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # geography(Point, 4326), nullable until geocoded
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)

    geocode_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/success/failed
    custom_radius_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class GeocodeJob(Base):
    __tablename__ = "geocode_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued/running/success/failed
    provider: Mapped[str] = mapped_column(String(40), default="google")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)

class TaskRun(Base):
    __tablename__ = "task_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    worker_id: Mapped[str] = mapped_column(String(120), nullable=False)

    # client reported location
    client_location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    distance_m: Mapped[float] = mapped_column(Numeric(10, 2))
    allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())