"""
Product routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from app.database import get_db
from app.models import Product, Source, PriceHistory, User
from app.schemas import (
    ProductCreate,
    ProductResponse,
    ProductDetail,
    PaginatedResponse,
    AggregateStats
)
from app.services.notifications import PriceHistoryService, NotificationService
from datetime import datetime

router = APIRouter(prefix="/api/products", tags=["products"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Get current user - simplified for demo"""
    # In production, extract from JWT token
    user = db.query(User).filter(User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user


@router.post("/", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product"""
    # Check for duplicate
    existing = db.query(Product).filter(
        Product.external_id == product_data.external_id,
        Product.source == product_data.source
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already exists from this source"
        )

    db_product = Product(
        **product_data.dict(),
        created_by_id=current_user.id,
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
    """List products with filtering and pagination"""
    query = db.query(Product)

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


@router.get("/{product_id}", response_model=ProductDetail)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed product information with price history"""
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Get price history
    price_history = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.recorded_at.desc()).all()

    product.price_history = price_history
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update product information"""
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Check for price change
    old_price = product.current_price
    if "current_price" in update_data and update_data["current_price"] != old_price:
        NotificationService.detect_price_change(
            db,
            product_id,
            update_data["current_price"],
            old_price
        )

        # Record new price in history
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


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a product"""
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}


@router.post("/{product_id}/refresh")
def refresh_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger a price refresh for a product (simulate API call)"""
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    product.last_fetched = datetime.utcnow()
    db.commit()

    return {
        "message": "Product refresh triggered",
        "product_id": product_id,
        "last_fetched": product.last_fetched
    }


@router.get("/analytics/overview")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregate analytics"""
    total_products = db.query(func.count(Product.id)).scalar() or 0

    products_by_source = db.query(
        Product.source,
        func.count(Product.id)
    ).group_by(Product.source).all()

    stats = AggregateStats(
        total_products=total_products,
        products_by_source={
            source.value: count
            for source, count in products_by_source
        },
        avg_price_by_category=PriceHistoryService.get_average_price_by_category(db),
        total_price_changes_today=0  # Would calculate from events
    )

    return stats
