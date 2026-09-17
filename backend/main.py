from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from database import Base, engine
from utils.seed import init_and_seed
from routers import auth, orders, drivers, vehicles, routes, ml, batches, simulation, analytics

init_and_seed()

app = FastAPI(
    title="IntelliRoute API",
    description="Intelligent Delivery & Logistics Optimization System",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5176",
    "http://localhost:5177",
    "http://127.0.0.1:5177",
    "http://localhost:5178",
    "http://127.0.0.1:5178",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allow_origins=[
    "https://intelliroute-frontend-dxdj.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request data",
            "errors": exc.errors(),
        },
    )

@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "A database error occurred. Please try again.",
        },
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected server error occurred.",
        },
    )

app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(drivers.router)
app.include_router(vehicles.router)
app.include_router(routes.router)
app.include_router(ml.router)
app.include_router(batches.router)
app.include_router(simulation.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "IntelliRoute API",
        "phase": 2,
    }

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
    }