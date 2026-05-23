from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_challenge1 import router as challenge1_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_dataset import router as dataset_router
from app.api.routes_demo import router as demo_router
from app.api.routes_impact import router as impact_router
from app.api.routes_layers import router as layers_router
from app.api.routes_optimizer import router as optimizer_router
from app.api.routes_operations import router as operations_router
from app.api.routes_recommendation import router as recommendation_router
from app.api.routes_regions import router as regions_router
from app.api.routes_scenarios import router as scenarios_router
from app.api.routes_simulation import router as simulation_router
from app.api.routes_truck_assignment import router as truck_assignment_router
from app.api.routes_zones import router as zones_router
from app.config import settings

app = FastAPI(title=settings.app_name, version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


app.include_router(dashboard_router)
app.include_router(challenge1_router)
app.include_router(dataset_router)
app.include_router(layers_router)
app.include_router(regions_router)
app.include_router(zones_router)
app.include_router(simulation_router)
app.include_router(truck_assignment_router)
app.include_router(optimizer_router)
app.include_router(operations_router)
app.include_router(recommendation_router)
app.include_router(scenarios_router)
app.include_router(demo_router)
app.include_router(impact_router)
