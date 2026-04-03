from app.database import SessionLocal, init_db
from app.models import Product, Source, PriceHistory, User
from app.utils.auth import get_password_hash, generate_api_key
from datetime import datetime

def seed_db():
    init_db()
    db = SessionLocal()
    
    # Create test user
    if not db.query(User).filter(User.email == "admin@entrupy.com").first():
        admin = User(
            email="admin@entrupy.com",
            hashed_password=get_password_hash("password123"),
            api_key=generate_api_key(),
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Created admin user: admin@entrupy.com / password123")

    # Create some products
    products = [
        {
            "external_id": "G1",
            "source": Source.GRAILED,
            "name": "Vintage Burberry Trench",
            "current_price": 450.0,
            "category": "Outerwear"
        },
        {
            "external_id": "F1",
            "source": Source.FASHIONPHILE,
            "name": "Chanel Flap Bag",
            "current_price": 5200.0,
            "category": "Bags"
        },
        {
            "external_id": "D1",
            "source": Source.ONESD_IBS,
            "name": "Rolex Submariner",
            "current_price": 12500.0,
            "category": "Watches"
        }
    ]

    for p_data in products:
        existing = db.query(Product).filter(
            Product.external_id == p_data["external_id"],
            Product.source == p_data["source"]
        ).first()
        
        if not existing:
            product = Product(**p_data, last_fetched=datetime.utcnow())
            db.add(product)
            db.commit()
            db.refresh(product)
            
            # Initial history
            history = PriceHistory(
                product_id=product.id,
                price=product.current_price,
                currency="USD"
            )
            db.add(history)
            db.commit()
            print(f"Added product: {product.name}")

    db.close()

if __name__ == "__main__":
    seed_db()
