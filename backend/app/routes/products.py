"""
Product routes — user-scoped
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models import Product, Source, PriceHistory, User
from app.schemas import (
    ProductCreate,
    ProductResponse,
    ProductDetail,
    PaginatedResponse,
    AggregateStats
)
from app.services.notifications import PriceHistoryService, NotificationService, WebhookDeliveryService
from app.utils.auth import verify_token
from datetime import datetime

router = APIRouter(prefix="/api/products", tags=["products"])


# ── Auth helper ──────────────────────────────────────────────────
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# ── Create ───────────────────────────────────────────────────────
@router.post("/", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product tied to the current user"""
    # Check for duplicate within the same user
    existing = db.query(Product).filter(
        Product.external_id == product_data.external_id,
        Product.source == product_data.source,
        Product.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already track this product from this source"
        )

    db_product = Product(
        **product_data.dict(),
        user_id=current_user.id,
        last_fetched=datetime.utcnow()
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    # Record initial price in history
    price_history = PriceHistory(
        product_id=db_product.id,
        price=product_data.current_price,
        currency=product_data.currency
    )
    db.add(price_history)
    db.commit()

    return db_product


# ── List (user-scoped) ───────────────────────────────────────────
@router.get("/", response_model=PaginatedResponse)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List only the current user's products"""
    query = db.query(Product).filter(Product.user_id == current_user.id)

    if source:
        try:
            source_enum = Source[source.upper()]
            query = query.filter(Product.source == source_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source. Must be one of: {', '.join([s.value for s in Source])}"
            )

    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))

    if min_price is not None:
        query = query.filter(Product.current_price >= min_price)

    if max_price is not None:
        query = query.filter(Product.current_price <= max_price)

    total = query.count()
    items = query.order_by(Product.updated_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "page": skip // limit,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit
    }


# ── Get single ───────────────────────────────────────────────────
@router.get("/{product_id}", response_model=ProductDetail)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed product info (must belong to current user)"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    price_history = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.recorded_at.desc()).all()

    product.price_history = price_history
    return product


# ── Update ───────────────────────────────────────────────────────
@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update product (user-scoped)"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    old_price = product.current_price
    if "current_price" in update_data and update_data["current_price"] != old_price:
        NotificationService.detect_price_change(db, product_id, update_data["current_price"], old_price)
        price_history = PriceHistory(
            product_id=product_id,
            price=update_data["current_price"],
            currency=update_data.get("currency", product.currency)
        )
        db.add(price_history)

    for key, value in update_data.items():
        if value is not None and hasattr(product, key):
            setattr(product, key, value)

    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return product


# ── Delete ───────────────────────────────────────────────────────
@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a product (user-scoped)"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


# ── Refresh (scrape) ─────────────────────────────────────────────
@router.post("/{product_id}/refresh")
async def refresh_product(
    product_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger a price refresh for a product"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    from app.services.scrapers import ScraperManager
    manager = ScraperManager()

    source_name = product.source.value if hasattr(product.source, "value") else str(product.source)
    scraped_data = await manager.refresh_product(source_name, product.external_id)

    if not scraped_data:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to refresh product from source")

    new_price = scraped_data.get("current_price")
    old_price = product.current_price

    if new_price is not None and new_price != old_price:
        event = NotificationService.detect_price_change(db, product_id, new_price, old_price)
        if event:
            background_tasks.add_task(WebhookDeliveryService.deliver_price_change, db, event.id)
        product.current_price = new_price
        price_history = PriceHistory(product_id=product_id, price=new_price, currency=product.currency)
        db.add(price_history)

    product.last_fetched = datetime.utcnow()
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)

    return {
        "message": "Product refresh successful",
        "product_id": product_id,
        "old_price": old_price,
        "new_price": product.current_price,
        "last_fetched": product.last_fetched
    }


# ── Analytics (user-scoped) ──────────────────────────────────────
@router.get("/analytics/overview")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregate analytics for the current user's products"""
    user_products = db.query(Product).filter(Product.user_id == current_user.id)
    total_products = user_products.count()

    products_by_source = db.query(
        Product.source,
        func.count(Product.id)
    ).filter(Product.user_id == current_user.id).group_by(Product.source).all()

    stats = AggregateStats(
        total_products=total_products,
        products_by_source={
            source.value: count
            for source, count in products_by_source
        },
        avg_price_by_category=PriceHistoryService.get_average_price_by_category(db, user_id=current_user.id),
        total_price_changes_today=0
    )

    return stats
