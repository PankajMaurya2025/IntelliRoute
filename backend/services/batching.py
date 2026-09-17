"""
Groups nearby pending orders into delivery batches using K-Means
clustering on delivery-point coordinates, then sequences each batch with
the Phase 1 TSP optimizer (greedy nearest-neighbor + 2-opt) to estimate
total distance/time. Batches and the order->batch link are persisted via
the existing Batch/Order models — no new tables.
"""
import math
from typing import List, Optional
import numpy as np
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session

from models import Order, Batch, OrderStatus
from algorithms.tsp import optimize_multi_stop

WAREHOUSE_COORDS = (18.5204, 73.8567)  # matches the seeded "Warehouse" location


def create_batches(db: Session, orders_per_batch: int = 4, warehouse: Optional[tuple] = None) -> List[Batch]:
    """
    Clusters all unbatched PENDING orders into groups of roughly
    `orders_per_batch` using K-Means, then creates a Batch row per cluster
    with a TSP-optimized total distance/time estimate.
    """
    warehouse = warehouse or WAREHOUSE_COORDS

    pending_orders = (
        db.query(Order)
        .filter(Order.status == OrderStatus.PENDING, Order.batch_id.is_(None))
        .all()
    )
    if len(pending_orders) < 2:
        return []  # nothing meaningful to batch

    coords = np.array([[o.delivery_lat, o.delivery_lng] for o in pending_orders])
    n_clusters = max(1, min(len(pending_orders), math.ceil(len(pending_orders) / max(1, orders_per_batch))))

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords)

    created_batches: List[Batch] = []
    for cluster_id in range(n_clusters):
        cluster_orders = [o for o, label in zip(pending_orders, labels) if label == cluster_id]
        if not cluster_orders:
            continue

        stops = [{"name": f"Order#{o.id}", "lat": o.delivery_lat, "lng": o.delivery_lng} for o in cluster_orders]
        tsp_result = optimize_multi_stop(stops, warehouse=warehouse)

        batch = Batch(
            total_distance_km=tsp_result["total_distance_km"],
            estimated_time_min=round((tsp_result["total_distance_km"] / 28.0) * 60.0, 1),  # 28 km/h avg
            num_orders=len(cluster_orders),
        )
        db.add(batch)
        db.flush()  # get batch.id before linking orders

        for order in cluster_orders:
            order.batch_id = batch.id

        created_batches.append(batch)

    db.commit()
    for b in created_batches:
        db.refresh(b)
    return created_batches
