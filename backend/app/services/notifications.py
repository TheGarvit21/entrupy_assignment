"""
Service for handling price change notifications and event management
"""
from sqlalchemy.orm import Session
from app.models import PriceChangeEvent, Product, PriceAlert, PriceHistory, Webhook
from datetime import datetime
from typing import List, Optional, Dict
import logging
import httpx
import asyncio

logger = logging.getLogger(__name__)


class WebhookDeliveryService:
    """Delivers notifications to configured webhooks"""
    
    @staticmethod
    async def deliver_price_change(db: Session, event_id: int):
        """Deliver a price change event to all active webhooks"""
        event = db.query(PriceChangeEvent).filter(PriceChangeEvent.id == event_id).first()
        if not event:
            return

        product = db.query(Product).filter(Product.id == event.product_id).first()
        if not product:
            return

        # Get all active webhooks
        webhooks = db.query(Webhook).filter(Webhook.is_active == True).all()

        payload = {
            "event": "price_change",
            "timestamp": event.detected_at.isoformat(),
            "product": {
                "id": product.id,
                "name": product.name,
                "source": product.source.value if hasattr(product.source, "value") else str(product.source),
                "url": product.url
            },
            "price": {
                "old": event.old_price,
                "new": event.new_price,
                "currency": product.currency
            }
        }

        async with httpx.AsyncClient() as client:
            tasks = []
            for webhook in webhooks:
                logger.info(f"Delivering price change event to {webhook.target_url}")
                tasks.append(WebhookDeliveryService._send_webhook(client, webhook.target_url, payload))
            
            await asyncio.gather(*tasks, return_exceptions=True)

        event.processed = True
        db.commit()

    @staticmethod
    async def _send_webhook(client, url, payload):
        """Send single webhook with basic retry"""
        for i in range(3): # 3 tries
            try:
                response = await client.post(url, json=payload, timeout=5.0)
                if response.status_code < 400:
                    return True
                logger.warning(f"Webhook delivery failed for {url}: {response.status_code}")
            except Exception as e:
                logger.warning(f"Webhook error for {url}: {str(e)}")
            
            if i < 2:
                await asyncio.sleep(1) # wait before retry
        return False


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
            db.refresh(event)
            logger.info(f"Price change detected for product {product_id}: {old_price} -> {new_price}")
            return event
        return None


class PriceHistoryService:
    """Handle price history queries and analytics"""

    @staticmethod
    def get_average_price_by_category(db: Session, user_id: Optional[int] = None) -> dict:
        """Get average price by category, optionally filtered by user"""
        from sqlalchemy import func

        query = db.query(
            Product.category,
            func.avg(Product.current_price).label("avg_price"),
            func.count(Product.id).label("count")
        )

        if user_id is not None:
            query = query.filter(Product.user_id == user_id)

        results = query.group_by(Product.category).all()

        return {
            row.category: {
                "average": round(float(row.avg_price), 2) if row.avg_price else 0,
                "count": row.count
            }
            for row in results if row.category
        }
