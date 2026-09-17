from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas.schemas import RouteRequest, RouteResponse
from utils.auth import get_current_user
from services.road_network import get_graph
from algorithms import route as run_route, ALGORITHMS
from algorithms.tsp import optimize_multi_stop

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.post("/optimize", response_model=RouteResponse)
def optimize_route(payload: RouteRequest, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    if payload.algorithm not in ALGORITHMS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown algorithm '{payload.algorithm}'. Choices: {list(ALGORITHMS.keys())}",
        )

    graph = get_graph(db)
    if payload.start not in graph.nodes:
        raise HTTPException(status_code=404, detail=f"Unknown start location '{payload.start}'")
    if payload.destination not in graph.nodes:
        raise HTTPException(status_code=404, detail=f"Unknown destination '{payload.destination}'")

    result = run_route(graph, payload.start, payload.destination, payload.algorithm)
    if not result.found:
        raise HTTPException(status_code=404, detail="No route found between these locations")

    return RouteResponse(**result.to_dict())


@router.get("/locations")
def list_locations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    graph = get_graph(db)
    return [{"name": n.name, "lat": n.lat, "lng": n.lng} for n in graph.nodes.values()]


@router.get("/algorithms")
def list_algorithms(current_user: User = Depends(get_current_user)):
    return {"algorithms": list(ALGORITHMS.keys())}


@router.post("/multi-stop")
def multi_stop_route(stops: list[dict], warehouse_lat: float, warehouse_lng: float,
                      current_user: User = Depends(get_current_user)):
    """Greedy nearest-neighbor + 2-opt sequencing for a driver with multiple orders."""
    if not stops:
        raise HTTPException(status_code=422, detail="At least one stop is required")
    return optimize_multi_stop(stops, (warehouse_lat, warehouse_lng))
