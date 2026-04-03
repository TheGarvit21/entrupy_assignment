from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index, Boolean, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class Source(str, enum.Enum):
    GRAILED = "grailed"
    FASHIONPHILE = "fashionphile"
    ONESD_IBS = "1stdibs"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_email", "email", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("idx_source_external_id", "source", "external_id", unique=True),
        Index("idx_category", "category"),
        Index("idx_price", "current_price"),
    )

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=False)
    source = Column(SQLEnum(Source), nullable=False)
    name = Column(String, nullable=False)
    url = Column(String)
    category = Column(String, index=True)
    description = Column(Text)
    current_price = Column(Float)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_fetched = Column(DateTime)

    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    price_alerts = relationship("PriceAlert", back_populates="product", cascade="all, delete-orphan")
    change_events = relationship("PriceChangeEvent", back_populates="product", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("idx_product_timestamp", "product_id", "recorded_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    product = relationship("Product", back_populates="price_history")


class PriceAlert(Base):
    __tablename__ = "price_alerts"
    __table_args__ = (
        Index("idx_product", "product_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    threshold_price = Column(Float)
    alert_type = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_alerts")


class PriceChangeEvent(Base):
    __tablename__ = "price_change_events"
    __table_args__ = (
        Index("idx_product_timestamp", "product_id", "detected_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    old_price = Column(Float)
    new_price = Column(Float, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed = Column(Boolean, default=False)

    product = relationship("Product", back_populates="change_events")


class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class RequestLog(Base):
    __tablename__ = "request_logs"
    __table_args__ = (
        Index("idx_timestamp", "requested_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    endpoint = Column(String)
    method = Column(String)
    status_code = Column(Integer)
    requested_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")
