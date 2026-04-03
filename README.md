# Product Price Monitoring System (Entrupy Internship Assignment)

## Overview
A comprehensive system for tracking product prices across multiple marketplaces (Grailed, Fashionphile, 1stDibs). 

## Technology Stack
- **Backend**: FastAPI, SQLAlchemy (SQLite), JWT for Auth
- **Frontend**: Vanilla JS (ES6+), Premium CSS Grid-based dark theme
- **Async Processing**: Python asyncio and FastAPI BackgroundTasks for scraping and notifications.

## Features
- **User Authentication**: Secure JWT-based auth stored in HTTPOnly cookies.
- **Product Tracking**: Automated scraping (with retry logic and exponential backoff).
- **Price History**: Millions of price points can be handled through indexed SQLite `price_history`.
- **Notifications**: Reliable webhook delivery with retry logic for price changes.
- **Analytics Dashboard**: Real-time stats by source and category.

## Setting Up

### Prerequisites
- Python 3.9+

### Installation
1.  **Backend Setup**:
    ```bash
    cd backend
    python -m venv venv
    ./venv/Scripts/activate # On Windows
    pip install -r requirements.txt
    python seed.py # Seeds admin user and initial data
    uvicorn app.main:app --reload
    ```
2.  **Frontend Setup**:
    Serve the `frontend` directory using any static file server (e.g. VS Code Live Server or `python -m http.server 8001`).

### Credentials
- **Admin Email**: `admin@entrupy.com`
- **Password**: `password123`

## API Documentation
- `POST /api/auth/register`: Create a new account
- `POST /api/auth/login`: Log in and receive a cookie
- `POST /api/auth/logout`: Log out and clear the cookie
- `GET /api/auth/me`: Current user profile (requires cookie)
- `GET /api/products/`: Paginated product list
- `POST /api/products/{id}/refresh`: Trigger an async price refresh
- `GET /api/products/analytics/overview`: Global statistics

## Design Rationale

### 1. Scaling Price History
To handle millions of rows, the `price_history` table uses a composite index on `(product_id, recorded_at)`. For even larger scales, a time-series database (like TimescaleDB) or partitioning by month/source would be implemented.

### 2. Notifications Architecture
I used **Webhooks** as the notification mechanism. When a price change is detected:
1.  An event is recorded in the `price_change_events` table.
2.  A `BackgroundTask` is spawned (non-blocking).
3.  The `WebhookDeliveryService` attempts delivery with a retry policy (up to 3 times with 1-second delay).
4.  This ensures reliability without slowing down the core scraping process.

### 3. Extending to 100+ Data Sources
I implemented a `ScraperManager` with a `BaseScraper` abstract class. Adding a new source only requires creating a 10-line concrete class. The use of `asyncio.gather` in the refresh process allows concurrent fetching across hundreds of sources efficiently.

## Limitations & Improvements
- **Rate Limiting**: Not yet implemented per-user; would use Redis for global rate-limiting.
- **Advanced Scraping**: Currently uses mocks; in production, I'd integrate Playwright or specialized proxy services.
- **Persistent Backend Tasks**: For massive scale, I'd replace `BackgroundTasks` with a dedicated worker (Celery/RQ).
