"""
Quant Trading API - FastAPI Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.stock import router as stock_router
from api.factors_strategies import router as fs_router

from api.yf import router as yf_router
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stock_router, prefix="/api", tags=["stock"])
app.include_router(fs_router, prefix="/api", tags=["factors-strategies"])
app.include_router(backtest_router, prefix="/api", tags=["backtest"])
app.include_router(yf_router, prefix="/api", tags=["yahoo-finance"])


@app.get("/")
def root():
    return {
        "message": "Quant Trading API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
