from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.detector import MicroplasticDetector
from backend.api import health, detect, analyses, auth, reports, model
from backend.db.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database automatically
    print("Starting API Server: Initializing database...")
    Base.metadata.create_all(bind=engine)
    
    # Load the YOLO model ONCE when the API server starts
    print("Starting API Server: Loading MicroplasticDetector model...")
    app.state.detector = MicroplasticDetector("weights/t29.pt")
    print("Model loaded successfully.")
    yield
    # Cleanup on shutdown (if needed)
    print("Shutting down API Server: Cleaning up model...")
    app.state.detector = None

app = FastAPI(
    title="Microplastic Detection API",
    description="Phase 4 FastAPI Backend with Auth & Database Persistence",
    version="1.0.0",
    lifespan=lifespan
)

# Allow the React development frontend to connect.
# Explicit origins only — do NOT reflect arbitrary origins. Authentication is
# via the Authorization header (JWT), not cookies, so credentialed CORS is not
# required here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the modular routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(detect.router, prefix="/api/v1", tags=["Detection"])
app.include_router(analyses.router, prefix="/api/v1", tags=["Analyses"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])
app.include_router(model.router, prefix="/api/v1", tags=["Model"])
