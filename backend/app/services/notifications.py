"""
Service for handling price change notifications and event management
"""
from sqlalchemy.orm import Session
from app.models import PriceChangeEvent, Product, PriceAlert, PriceHistory, Source
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Handle price change notifications"""

    @staticmethod
    def detect_price_change(
        db: Session,
        product_id: int,
        new_price: float,
        old_price: Optional[float]
    ) -> Optional[PriceChangeEvent]:
        """
        Detect if price has changed and create event
        Returns PriceChangeEvent if price changed, None otherwise
        """
        if old_price is None or old_price != new_price:
            event = PriceChangeEvent(
                product_id=product_id,
                old_price=old_price,
                new_price=new_price,
                detected_at=datetime.utcnow(),
                processed=False
            )
            db.add(event)
            db.commit()
            logger.info(f"Price change detected for product {product_id}: {old_price} -> {new_price}")
            return event
        return None

    @staticmethod
    def get_unprocessed_events(db: Session, limit: int = 100) -> List[PriceChangeEvent]:
        """Get unprocessed price change events"""
        return db.query(PriceChangeEvent).filter(
            PriceChangeEvent.processed == False
        ).limit(limit).all()

    @staticmethod
    def mark_event_processed(db: Session, event_id: int):
        """Mark event as processed"""
        event = db.query(PriceChangeEvent).filter(PriceChangeEvent.id == event_id).first()
        if event:
            event.processed = True
            db.commit()

    @staticmethod
    def check_alert_triggers(db: Session, product_id: int, new_price: float):
        """Check which alerts should be triggered for a product price change"""
        alerts = db.query(PriceAlert).filter(
            PriceAlert.product_id == product_id,
            PriceAlert.is_active == True
        ).all()

        triggered_alerts = []
        for alert in alerts:
            should_trigger = False

            if alert.alert_type == "any_change":
                should_trigger = True
            elif alert.alert_type == "price_drop" and alert.threshold_price:
                should_trigger = new_price <= alert.threshold_price
            elif alert.alert_type == "price_increase" and alert.threshold_price:
                should_trigger = new_price >= alert.threshold_price

            if should_trigger:
                triggered_alerts.append(alert)

        return triggered_alerts


class PriceHistoryService:
    """Handle price history queries and analytics"""

    @staticmethod
    def get_price_history(
        db: Session,
        product_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[PriceHistory], int]:
        """Get price history for a product with pagination"""
        query = db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id
        ).order_by(PriceHistory.recorded_at.desc())

        total = query.count()
        history = query.limit(limit).offset(offset).all()

        return history, total

    @staticmethod
    def get_average_price_by_category(db: Session) -> dict:
        """Get average price by category"""
        from sqlalchemy import func

        results = db.query(
            Product.category,
            func.avg(Product.current_price).label("avg_price"),
            func.count(Product.id).label("count")
        ).group_by(Product.category).all()

        return {
            row.category: {
                "average": row.avg_price,
                "count": row.count
            }
            for row in results if row.category
        }

    @staticmethod
    def get_price_stats_by_source(db: Session) -> dict:
        """Get price statistics by source"""
        from sqlalchemy import func

        results = db.query(
            Product.source,
            func.count(Product.id).label("count"),
            func.avg(Product.current_price).label("avg_price"),
            func.min(Product.current_price).label("min_price"),
            func.max(Product.current_price).label("max_price")
        ).group_by(Product.source).all()

        return {
            row.source.value: {
                "count": row.count,
                "average": row.avg_price,
                "min": row.min_price,
                "max": row.max_price
            }
            for row in results
        }


class SyncService:
    """Handle data fetching and syncing from marketplaces"""

    @staticmethod
    async def fetch_price_data(user_id: int, db: Session) -> dict:
        """
        Simulate fetching price data from marketplaces
        In production, this would call actual marketplace APIs
        """
        logger.info(f"Syncing price data for user {user_id}")

        # This would connect to marketplace APIs
        # For now, return a summary
        products_updated = 0
        price_changes_detected = 0

        return {
            "products_updated": products_updated,
            "price_changes_detected": price_changes_detected,
            "timestamp": datetime.utcnow()
        }
