"""
Seeds the database with demo data so the app is immediately explorable:
1 admin user, a small road network (warehouse + delivery locations with
realistic-looking Pune coordinates), 5 vehicles, 5 drivers, 10+ orders.

Run directly: python -m utils.seed   (or it's called automatically on
first startup by main.py if the users table is empty).
"""
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import (
    User, Location, RouteEdge, Vehicle, Driver, Order, TrafficEvent,
    OrderStatus, VehicleStatus, DriverStatus, TrafficLevel,
)
from utils.auth import hash_password

# name -> (lat, lng); loosely based on real Pune-area geography
LOCATIONS = {
    "Warehouse": (18.5204, 73.8567),
    "Koregaon Park": (18.5362, 73.8939),
    "Viman Nagar": (18.5679, 73.9143),
    "Hinjewadi": (18.5912, 73.7389),
    "Baner": (18.5590, 73.7868),
    "Kothrud": (18.5074, 73.8077),
    "Hadapsar": (18.5089, 73.9260),
    "Camp": (18.5122, 73.8792),
    "Aundh": (18.5643, 73.8077),
    "Wakad": (18.5985, 73.7627),
}

# (from, to, distance_km, base_time_min) — a connected road graph, not a complete graph
ROADS = [
    ("Warehouse", "Camp", 3.0, 8.0),
    ("Warehouse", "Kothrud", 4.5, 12.0),
    ("Camp", "Koregaon Park", 2.5, 7.0),
    ("Koregaon Park", "Viman Nagar", 4.0, 11.0),
    ("Camp", "Hadapsar", 5.0, 14.0),
    ("Kothrud", "Baner", 6.0, 16.0),
    ("Baner", "Aundh", 3.0, 8.0),
    ("Aundh", "Wakad", 4.0, 10.0),
    ("Wakad", "Hinjewadi", 3.5, 9.0),
    ("Baner", "Hinjewadi", 7.0, 18.0),
    ("Warehouse", "Aundh", 6.5, 17.0),
    ("Viman Nagar", "Hadapsar", 6.0, 16.0),
]


def seed(db: Session):
    if db.query(User).first():
        print("Database already seeded — skipping.")
        return

    # --- demo user ---
    demo_user = User(
        name="Demo Admin",
        email="admin@intelliroute.com",
        hashed_password=hash_password("Admin@123"),
        role="admin",
    )
    db.add(demo_user)

    # --- locations (graph nodes) ---
    for name, (lat, lng) in LOCATIONS.items():
        db.add(Location(name=name, latitude=lat, longitude=lng, is_warehouse=(name == "Warehouse")))

    # --- roads (graph edges, both directions) ---
    for a, b, dist, time in ROADS:
        db.add(RouteEdge(from_location=a, to_location=b, distance_km=dist, base_travel_time_min=time, traffic_factor=1.0))
        db.add(RouteEdge(from_location=b, to_location=a, distance_km=dist, base_travel_time_min=time, traffic_factor=1.0))

    db.commit()

    # --- traffic events (also bump traffic_factor on the matching road edges,
    #     so seeded traffic actually affects routing, not just a log table) ---
    traffic_defs = [
        ("Warehouse", "Kothrud", TrafficLevel.HIGH, 1.7),
        ("Baner", "Hinjewadi", TrafficLevel.SEVERE, 2.3),
        ("Camp", "Hadapsar", TrafficLevel.MEDIUM, 1.3),
        ("Aundh", "Wakad", TrafficLevel.MEDIUM, 1.3),
    ]
    for a, b, level, factor in traffic_defs:
        db.add(TrafficEvent(from_location=a, to_location=b, level=level))
        for edge in db.query(RouteEdge).filter(
            ((RouteEdge.from_location == a) & (RouteEdge.to_location == b)) |
            ((RouteEdge.from_location == b) & (RouteEdge.to_location == a))
        ).all():
            edge.traffic_factor = factor
    db.commit()

    # --- vehicles ---
    vehicle_defs = [
        ("PUN-BK-101", "bike", 15.0),
        ("PUN-BK-102", "bike", 15.0),
        ("PUN-CR-201", "car", 60.0),
        ("PUN-VN-301", "van", 150.0),
        ("PUN-BK-103", "bike", 15.0),
    ]
    vehicles = []
    for number, vtype, cap in vehicle_defs:
        v = Vehicle(vehicle_number=number, vehicle_type=vtype, capacity_kg=cap,
                    status=VehicleStatus.AVAILABLE, fuel_level=90.0,
                    current_lat=LOCATIONS["Warehouse"][0], current_lng=LOCATIONS["Warehouse"][1])
        db.add(v)
        vehicles.append(v)
    db.commit()
    for v in vehicles:
        db.refresh(v)

    # --- drivers (one per vehicle) ---
    driver_names = ["Rohit Sharma", "Ananya Iyer", "Vikram Singh", "Priya Nair", "Arjun Mehta"]
    drivers = []
    for name, vehicle in zip(driver_names, vehicles):
        d = Driver(
            name=name, phone="+91-90000-000" + str(len(drivers) + 1),
            status=DriverStatus.AVAILABLE,
            current_lat=LOCATIONS["Warehouse"][0], current_lng=LOCATIONS["Warehouse"][1],
            vehicle_id=vehicle.id, rating=4.5,
        )
        db.add(d)
        drivers.append(d)
    db.commit()

    # --- orders (10+, mixed priority, across delivery locations) ---
    customer_names = [
        "Aarav Patel", "Ishita Rao", "Kabir Malhotra", "Sanya Kapoor", "Dev Joshi",
        "Meera Pillai", "Rahul Verma", "Tanya Bhatt", "Yusuf Khan", "Neha Agarwal",
        "Karan Chawla", "Divya Menon",
    ]
    delivery_points = list(LOCATIONS.keys())
    delivery_points.remove("Warehouse")
    priorities = [1, 2, 3, 3, 4, 2, 3, 1, 4, 3, 2, 3]

    for i, name in enumerate(customer_names):
        dest = delivery_points[i % len(delivery_points)]
        dlat, dlng = LOCATIONS[dest]
        order = Order(
            customer_name=name,
            pickup_location="Warehouse",
            pickup_lat=LOCATIONS["Warehouse"][0],
            pickup_lng=LOCATIONS["Warehouse"][1],
            delivery_location=dest,
            delivery_lat=dlat,
            delivery_lng=dlng,
            priority=priorities[i],
            package_weight_kg=round(1.0 + (i % 5) * 1.5, 1),
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        db.add(order)

    db.commit()
    print("Seed complete:")
    print(f"  - 1 demo user   (admin@intelliroute.com / Admin@123)")
    print(f"  - {len(LOCATIONS)} locations, {len(ROADS) * 2} directional road edges")
    print(f"  - {len(traffic_defs)} traffic events (applied to matching road edges)")
    print(f"  - {len(vehicles)} vehicles, {len(drivers)} drivers")
    print(f"  - {len(customer_names)} orders")


def init_and_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_and_seed()
