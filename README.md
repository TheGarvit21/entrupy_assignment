# Product Price Monitoring System

Tracks competitor pricing across Grailed, Fashionphile, and 1stDibs. Each user sees only their own products. Prices are stored over time with change detection and webhook notifications.

---

## Stack

- **Backend** — FastAPI, SQLAlchemy, SQLite, bcrypt, python-jose, uvicorn
- **Frontend** — HTML, CSS, Vanilla JS (no framework)
- **Tests** — pytest, FastAPI TestClient

---

## Setup

**1. Clone**
```bash
git clone https://github.com/TheGarvit21/entrupy_assignment.git
cd entrupy_assignment
```

**2. Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**3. Create `.env` inside `backend/`**
```env
SECRET_KEY=any-long-random-string
DATABASE_URL=sqlite:///./price_monitoring.db
CORS_ORIGINS=["http://127.0.0.1:5500"]
```

**4. Start the server**
```bash
uvicorn app.main:app --reload
```
API runs at `http://127.0.0.1:8000` — Swagger docs at `/docs`

**5. Seed sample data (optional)**
```bash
python seed.py
```

**6. Start the frontend**

Open `frontend/` in VS Code and use Live Server (right-click `index.html` → Open with Live Server).
Make sure it serves from `127.0.0.1:5500`, not `localhost:5500` — matters for cookies.

---

## Running Tests
```bash
cd backend
python -m pytest tests/ -v
```

---

## Using the App

| Action | How |
|---|---|
| Register | Click "Access Platform" → "Create account" → submit → auto-redirected to login |
| Login | Enter credentials → "Sign In" |
| Dashboard | Shows total products, sources, price changes, average value + bar charts |
| Add product | Products page → "+ Add New Product" → fill modal → submit |
| Filter products | Use search, dropdowns, and price range inputs → Apply |
| View price history | Click any product name in the table |
| Sync price | Click "Sync" on a product row to re-fetch latest price |
| Delete product | Click "Drop" on a product row |
| Analytics | Click "Analytics" in navbar → per-source counts and per-category averages |
| Logout | Click "Logout" in the top-right |

---

## API Reference

### System

| Method | Path | Description |
|---|---|---|
| GET | `/` | API info |
| GET | `/health` | Health check |

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account — body: `{email, password}` |
| POST | `/api/auth/login` | Login, sets HttpOnly cookie — body: `{email, password}` |
| POST | `/api/auth/logout` | Clear session cookie |
| GET | `/api/auth/me` | Get current user profile |

### Products (all require login)

| Method | Path | Description |
|---|---|---|
| POST | `/api/products/` | Add product — body: `{external_id, source, name, current_price, ...}` |
| GET | `/api/products/` | List own products — params: `skip, limit, source, category, min_price, max_price` |
| GET | `/api/products/{id}` | Product detail with full price history |
| DELETE | `/api/products/{id}` | Remove product permanently |
| POST | `/api/products/{id}/refresh` | Re-scrape price from marketplace |
| GET | `/api/products/analytics/overview` | Aggregate stats — totals, per-source, per-category averages |

### Source values
`grailed` / `fashionphile` / `1stdibs`

---

## Notes

- Passwords are bcrypt-hashed, never stored plain
- Products are user-scoped — two users can track the same listing independently
- Price changes trigger a `PriceChangeEvent` and fire registered webhooks asynchronously
- For production: use PostgreSQL, HTTPS cookies, and replace mock scrapers with Playwright
