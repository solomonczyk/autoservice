from datetime import datetime
from typing import Optional, List
from sqlalchemy import ForeignKey, DateTime, String, Integer, Float, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.session import Base

class AppointmentStatus(str, enum.Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(500))

    appointments: Mapped[List["Appointment"]] = relationship(back_populates="shop")
    users: Mapped[List["User"]] = relationship(back_populates="shop")

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole), 
        default=UserRole.STAFF,
        nullable=False
    )

    # Tenant Integrity: A user belongs to a Shop (Tenant)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"))
    shop: Mapped["Shop"] = relationship(back_populates="users")

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    vehicle_info: Mapped[Optional[str]] = mapped_column(String(500))

    appointments: Mapped[List["Appointment"]] = relationship(back_populates="client")

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    base_price: Mapped[float] = mapped_column(Float)

    appointments: Mapped[List["Appointment"]] = relationship(back_populates="service")

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLAlchemyEnum(AppointmentStatus), 
        default=AppointmentStatus.NEW,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    shop: Mapped["Shop"] = relationship(back_populates="appointments")
    client: Mapped["Client"] = relationship(back_populates="appointments")
    service: Mapped["Service"] = relationship(back_populates="appointments")
