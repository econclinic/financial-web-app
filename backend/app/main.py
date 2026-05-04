from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import auth, market, market_data, portfolio, watchlist
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(market_data.router, prefix="/api/market-data", tags=["market-data"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
