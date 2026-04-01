# Product Price Monitoring System

A full-stack application to monitor product prices across multiple marketplaces (Grailed, Fashionphile, 1stDibs) with real-time analytics and price tracking.

Features

- **Product Management** - Add, view, update, and delete products
- **Price Tracking** - Monitor price changes with historical data
- **Analytics Dashboard** - View statistics by source and category
- **Multi-Source Support** - Track products from Grailed, Fashionphile, 1stDibs
- **No Authentication** - Fully open API for easy access
- **Pagination Support** - Efficiently handle large product lists

Prerequisites

- Python 3.8+
- Node.js (for frontend development)
- SQLite (included)

 Setup & Installation

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
python -m app.main
```

Server runs on: **http://localhost:8000**

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Open in browser:
- Double-click `index.html` or
- Use a local server: `python -m http.server 8001`

Access on: **http://localhost:8001** (or file path)

## API Endpoints

All endpoints are prefixed with `/api`

### Core Endpoints

#### **Health Check**
```
GET /health
```
Returns server status and timestamp.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00"
}
```

---

### Product Endpoints

#### **1. Get All Products (with filtering & pagination)**
```
GET /api/products/
```

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| skip | integer | Number of products to skip | 0 |
| limit | integer | Number of products to return | 20 |
| source | string | Filter by source (grailed, fashionphile, 1stdibs) | optional |
| category | string | Filter by category (partial match) | optional |
| min_price | float | Minimum price filter | optional |
| max_price | float | Maximum price filter | optional |

**Example Request:**
```
GET /api/products/?skip=0&limit=20&source=grailed&min_price=100&max_price=500
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "external_id": "ext123",
      "source": "grailed",
      "name": "Designer Jacket",
      "url": "https://example.com/jacket",
      "category": "Clothing",
      "current_price": 250.00,
      "currency": "USD",
      "updated_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 100,
  "page": 0,
  "page_size": 20,
  "total_pages": 5
}
```

---

#### **2. Get Single Product with Price History**
```
GET /api/products/{product_id}
```

**Path Parameters:**
- `product_id` (integer) - Product ID

**Example Request:**
```
GET /api/products/1
```

**Response:**
```json
{
  "id": 1,
  "external_id": "ext123",
  "source": "grailed",
  "name": "Designer Jacket",
  "url": "https://example.com/jacket",
  "category": "Clothing",
  "description": "Authentic designer jacket",
  "current_price": 250.00,
  "currency": "USD",
  "created_at": "2024-01-10T08:00:00",
  "updated_at": "2024-01-15T10:30:00",
  "last_fetched": "2024-01-15T10:30:00",
  "price_history": [
    {
      "id": 1,
      "price": 300.00,
      "currency": "USD",
      "recorded_at": "2024-01-10T08:00:00"
    },
    {
      "id": 2,
      "price": 250.00,
      "currency": "USD",
      "recorded_at": "2024-01-15T10:30:00"
    }
  ]
}
```

---

#### **3. Create New Product**
```
POST /api/products/
```

**Request Body:**
```json
{
  "external_id": "ext123",
  "source": "grailed",
  "name": "Designer Jacket",
  "url": "https://example.com/jacket",
  "category": "Clothing",
  "description": "Authentic designer jacket",
  "current_price": 250.00,
  "currency": "USD"
}
```

**Response:**
```json
{
  "id": 1,
  "external_id": "ext123",
  "source": "grailed",
  "name": "Designer Jacket",
  "url": "https://example.com/jacket",
  "category": "Clothing",
  "current_price": 250.00,
  "currency": "USD",
  "updated_at": "2024-01-15T10:30:00"
}
```

---

#### **4. Update Product**
```
PUT /api/products/{product_id}
```

**Path Parameters:**
- `product_id` (integer) - Product ID

**Request Body:**
```json
{
  "current_price": 220.00,
  "category": "Designer Wear",
  "description": "Updated description"
}
```

**Response:** Updated product object (same as create)

---

#### **5. Delete Product**
```
DELETE /api/products/{product_id}
```

**Path Parameters:**
- `product_id` (integer) - Product ID

**Response:**
```json
{
  "message": "Product deleted successfully"
}
```

---

#### **6. Refresh Product**
```
POST /api/products/{product_id}/refresh
```

**Path Parameters:**
- `product_id` (integer) - Product ID

**Response:**
```json
{
  "message": "Product refresh triggered",
  "product_id": 1,
  "last_fetched": "2024-01-15T10:30:00"
}
```

---

#### **7. Get Analytics Overview**
```
GET /api/products/analytics/overview
```

**Response:**
```json
{
  "total_products": 50,
  "products_by_source": {
    "grailed": 20,
    "fashionphile": 15,
    "1stdibs": 15
  },
  "avg_price_by_category": {
    "Clothing": {
      "average": 250.50,
      "count": 25
    },
    "Accessories": {
      "average": 150.00,
      "count": 25
    }
  },
  "total_price_changes_today": 8
}
```

---

## 🎯 Supported Data Sources

| Source | ID | Description |
|--------|-----|-------------|
| Grailed | `grailed` | Fashion marketplace |
| Fashionphile | `fashionphile` | Luxury resale |
| 1stDibs | `1stdibs` | Vintage & design collectibles |

---

## 📝 Example Usage

### Add a Product
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "ABC123",
    "source": "grailed",
    "name": "Vintage Watch",
    "current_price": 500.00,
    "currency": "USD",
    "category": "Watches"
  }'
```

### Get All Products
```bash
curl http://localhost:8000/api/products/?limit=10&source=grailed
```

### Get Product Details
```bash
curl http://localhost:8000/api/products/1
```

### Update Price
```bash
curl -X PUT http://localhost:8000/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"current_price": 450.00}'
```

### Delete Product
```bash
curl -X DELETE http://localhost:8000/api/products/1
```

### Get Analytics
```bash
curl http://localhost:8000/api/products/analytics/overview
```

---

## 📊 Database Schema

### Products Table
```
id (Primary Key)
external_id (String, unique per source)
source (Enum: grailed, fashionphile, 1stdibs)
name (String)
url (String, optional)
category (String, optional)
description (Text, optional)
current_price (Float)
currency (String, default: USD)
created_at (DateTime)
updated_at (DateTime)
last_fetched (DateTime, optional)
```

### Price History Table
```
id (Primary Key)
product_id (Foreign Key → Products)
price (Float)
currency (String)
recorded_at (DateTime)
```

### Price Alerts Table
```
id (Primary Key)
product_id (Foreign Key → Products)
threshold_price (Float, optional)
alert_type (String)
is_active (Boolean)
created_at (DateTime)
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=sqlite:///./price_monitoring.db

# CORS Origins
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Server
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 📱 Frontend Features

### Dashboard
- View total products, data sources, price changes, average prices
- Charts showing products by source and average price by category

### Products
- Browse all products with filtering (source, category, price range)
- Add new products from marketplace
- View detailed product information
- Edit and delete products
- Search functionality
- Pagination support

### Analytics
- Price statistics by source and category
- Visual representations of data

---

## 🐛 Error Handling

All errors return appropriate HTTP status codes:

| Status | Description |
|--------|-------------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Product doesn't exist |
| 500 | Internal Server Error |

**Error Response Format:**
```json
{
  "detail": "Error message here"
}
```

---

## 📂 Project Structure

```
entrupy/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── models.py         # Database models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── database.py       # DB connection
│   │   ├── routes/
│   │   │   └── products.py   # Product endpoints
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utilities
│   ├── requirements.txt
│   └── price_monitoring.db   # SQLite database
│
├── frontend/
│   ├── index.html            # Main page
│   ├── js/
│   │   ├── api.js           # API calls
│   │   ├── app.js           # Application logic
│   │   └── ui.js            # UI functions
│   └── css/
│       └── styles.css       # Styling
│
└── README.md
```

---

## 🚀 Quick Start

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

**Frontend:**
```bash
# Open frontend/index.html in browser
# Or run a local server
cd frontend
python -m http.server 8001
```

Then open: **http://localhost:8001**

---

## 📄 License

This project is open source and available under the MIT License.

---

## ✅ Notes

- **No Authentication Required** - All endpoints are publicly accessible
- **SQLite Database** - Lightweight, no external database needed
- **Auto-reload** - Backend auto-reloads on code changes
- **CORS Enabled** - Frontend can communicate with backend
- **Real-time Updates** - Price history tracked automatically

---

## 📞 Support

For issues or questions, check the endpoints documentation above or review the API response examples.
