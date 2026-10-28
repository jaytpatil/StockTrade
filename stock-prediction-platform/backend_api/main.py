import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models
from routes import auth_routes, stock_routes, admin, websocket_routes, trading_routes

# Create DB Tables
Base.metadata.create_all(bind=engine)

def auto_migrate():
    """Ensure newly added columns exist in users table without requiring manual DB reset."""
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            if engine.url.drivername.startswith("sqlite"):
                cursor = conn.execute(text("PRAGMA table_info(users)"))
                cols = [row[1] for row in cursor.fetchall()]
                if "virtual_balance" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN virtual_balance FLOAT DEFAULT 100000.0"))
                if "is_guest" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_guest BOOLEAN DEFAULT 0"))
                if "full_name" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR DEFAULT 'Trader'"))
                conn.commit()
        except Exception as e:
            print("Auto-migrate note:", e)

auto_migrate()

def seed_demo_user():
    from database import SessionLocal
    import auth
    db = SessionLocal()
    try:
        demo_email = "demo@trader.com"
        existing = db.query(models.User).filter(models.User.email == demo_email).first()
        if not existing:
            demo_user = models.User(
                email=demo_email,
                hashed_password=auth.get_password_hash("password123"),
                full_name="Demo Trader",
                virtual_balance=100000.0,
                is_guest=False
            )
            db.add(demo_user)
            db.commit()
    except Exception as e:
        print("Seed user note:", e)
    finally:
        db.close()

seed_demo_user()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the websocket broadcaster
    task = asyncio.create_task(websocket_routes.stock_data_broadcaster())
    yield
    # Cancel the task on shutdown
    task.cancel()

app = FastAPI(
    title="StockTrade Backend API",
    description="StockTrade AI prediction & paper trading API.",
    version="2.0.0",
    lifespan=lifespan
)

@app.get("/")
def root_status():
    return {
        "status": "online",
        "message": "StockTrade API is active.",
        "documentation": "/docs",
        "version": "2.0.0"
    }

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import APIRouter

# Create an api router
api_router = APIRouter()

# Includes as requested exactly
api_router.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])

# The prompt requested /stocks for history, list, indicators. 
# And /predict/{symbol}, /recommend/{symbol} directly at root or under stocks. 
# I will map predicting/recommending locally off the stock_routes or root:
api_router.include_router(stock_routes.router, prefix="/stocks", tags=["Stocks (Basic)"])
# Map the /predict and /recommend to the same router but at root
api_router.include_router(stock_routes.router, tags=["Predictions"])

# Include the websocket router
app.include_router(websocket_routes.router)

from app.api import news

api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(news.router, prefix="/news", tags=["News"])
api_router.include_router(trading_routes.router, prefix="/trade", tags=["Paper Trading & Wallet"])

# Mount api_router under /api/v1
app.include_router(api_router, prefix="/api/v1")
