"""
Builds the in-memory routing Graph from the locations/route_edges tables,
and keeps it cached. Traffic simulation updates mutate this same graph so
routing always reflects current traffic factors.
"""
from sqlalchemy.orm import Session

from algorithms import Graph
from models import Location, RouteEdge

_graph_cache: Graph = None


def build_graph(db: Session) -> Graph:
    g = Graph()
    for loc in db.query(Location).all():
        g.add_node(loc.name, loc.latitude, loc.longitude)
    for edge in db.query(RouteEdge).all():
        g.add_edge(
            edge.from_location, edge.to_location,
            edge.distance_km, edge.base_travel_time_min, edge.traffic_factor,
            bidirectional=False,  # edges are stored directionally in DB already (seeded both ways)
        )
    return g


def get_graph(db: Session, refresh: bool = False) -> Graph:
    global _graph_cache
    if _graph_cache is None or refresh:
        _graph_cache = build_graph(db)
    return _graph_cache


def invalidate_graph_cache():
    global _graph_cache
    _graph_cache = None
