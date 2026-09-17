# IntelliRoute — Complete Delivery & Logistics Management System

A **real, runnable** FastAPI backend for a delivery/logistics platform:
database, auth, a hand-written DSA routing engine, priority-queue dispatch,
CRUD APIs (Phase 1) — plus ML-based ETA prediction, K-Means order batching,
a WebSocket-driven live delivery simulation, and analytics (Phase 2). 

## What's actually implemented (no placeholders)

**Phase 1:**
- **PostgreSQL (Supabase) + SQLAlchemy** — 10 tables (`users`, `locations`,
  `route_edges`, `vehicles`, `drivers`, `orders`, `deliveries`, `batches`,
  `traffic_events`, `simulation_runs`), auto-created on first run.
  *(As of Phase 2, SQLite is no longer supported — see "Database" below.)*
- **JWT auth** with bcrypt password hashing (`passlib`) — signup, login,
  protected routes via `Depends(get_current_user)`.
- **DSA algorithms**, all hand-written, no shortcuts:
  - `algorithms/priority_queue.py` — real binary min-heap (`heapq`) backed
    priority queue for order dispatch (1=Emergency … 4=Low).
  - `algorithms/graph.py` — Dijkstra, A* (haversine heuristic), BFS, DFS,
    Bellman-Ford, Floyd-Warshall, all behind one `route(graph, start, dest, algorithm)`
    interface.
  - `algorithms/tsp.py` — greedy nearest-neighbor construction + 2-opt local
    search for multi-stop driver routes.
- **REST API** — `/api/auth/*`, `/api/orders/*`, `/api/drivers/*`,
  `/api/vehicles/*`, `/api/routes/*`.
- **Error handling** — global handlers so the API never leaks raw Python
  tracebacks.

**Phase 2 (new):**
- **ML ETA prediction** (`ml/`) — `generate_data.py` synthesizes 4,000
  realistic training rows (distance, traffic, stops, priority, weight,
  hour, day-of-week -> ETA minutes, with a deliberately non-linear
  relationship: multiplicative traffic effect, rush-hour surcharge,
  per-stop overhead, diminishing-returns weight penalty, noise).
  `train_model.py` trains a `RandomForestRegressor` and saves it with
  `joblib`. `predict.py` loads (or trains, if missing) the model and
  exposes `predict_eta()`. **Actually trained and tested in the sandbox
  I built this in: MAE 3.3 minutes, R² 0.97** — see "Verification status".
- **K-Means batching** (`services/batching.py`) — clusters unbatched
  pending orders by delivery coordinates with scikit-learn `KMeans`,
  sequences each cluster with the Phase 1 TSP optimizer, and persists the
  result via the existing `Batch`/`Order` models (no new tables).
- **WebSocket live simulation** (`simulation/engine.py` +
  `routers/simulation.py`) — a pure-Python engine moves each assigned
  order's driver along a real Dijkstra-resolved route (interpolating
  lat/lng between waypoints by elapsed distance), broadcasting state once
  per second over `/ws/simulation`. REST controls: `/api/simulation/start
  |pause|resume|stop|reset|state`.
- **Analytics** (`routers/analytics.py`) — `GET /api/analytics/summary`:
  order counts by status, driver/vehicle utilization, average ETA, total
  distance, priority breakdown — all live SQL aggregates, no hard-coded
  numbers.

## Project structure

```
intelliroute/
├── README.md
├── .gitignore
└── backend/
    ├── main.py, database.py, requirements.txt, .env.example
    ├── models/       → models.py (10 tables, 5 enums — unchanged since Phase 1)
    ├── schemas/      → schemas.py (Phase 1 schemas + Phase 2 additions: TrainModelResponse,
    │                    BatchCreateRequest/Out/DetailOut, SimulationControlResponse,
    │                    AnalyticsSummary, PriorityBreakdown)
    ├── algorithms/   → graph.py, priority_queue.py, tsp.py (unchanged since Phase 1)
    ├── ml/           → generate_data.py, train_model.py, predict.py (NEW)
    ├── simulation/   → engine.py (NEW — pure-Python movement engine)
    ├── services/     → road_network.py, dispatch.py (Phase 1)
    │                    batching.py (NEW — K-Means + TSP)
    ├── routers/      → auth.py, orders.py, drivers.py, vehicles.py, routes.py (Phase 1)
    │                    ml.py, batches.py, simulation.py, analytics.py (NEW)
    ├── utils/        → auth.py (unchanged), seed.py (updated: + traffic events)
    └── tests/
        ├── conftest.py            # REWRITTEN for Phase 2 — see "Testing" below
        ├── test_algorithms.py     # Phase 1, unchanged
        ├── test_api.py            # Phase 1, unchanged
        ├── test_ml.py             # NEW
        ├── test_batching.py       # NEW
        ├── test_simulation.py     # NEW
        └── test_analytics.py      # NEW
```

## Files to replace vs. create (if merging into an existing Phase 1 checkout)

**Replace these existing files:**
- `backend/main.py` — added 4 router imports/includes, updated title/version/root response
- `backend/database.py` — now requires PostgreSQL; raises on missing/SQLite `DATABASE_URL`
- `backend/schemas/schemas.py` — appended Phase 2 schemas (nothing removed)
- `backend/requirements.txt` — added `psycopg2-binary`, `pytest-asyncio`
- `backend/.env.example` — SQLite line replaced with Supabase connection string + `TEST_DATABASE_URL`
- `backend/utils/seed.py` — added traffic-event seeding (applies `traffic_factor` to matching roads)
- `backend/tests/conftest.py` — rewritten for a Postgres test database instead of a throwaway SQLite file

**New files:**
- `backend/ml/__init__.py`, `ml/generate_data.py`, `ml/train_model.py`, `ml/predict.py`
- `backend/simulation/__init__.py`, `simulation/engine.py`
- `backend/services/batching.py`
- `backend/routers/ml.py`, `routers/batches.py`, `routers/simulation.py`, `routers/analytics.py`
- `backend/tests/test_ml.py`, `tests/test_batching.py`, `tests/test_simulation.py`, `tests/test_analytics.py`

**Untouched from Phase 1:** `models/`, `algorithms/`, `routers/auth.py`,
`routers/orders.py`, `routers/drivers.py`, `routers/vehicles.py`,
`routers/routes.py`, `services/road_network.py`, `services/dispatch.py`,
`utils/auth.py`, `tests/test_algorithms.py`, `tests/test_api.py`.

## Database: moving to Supabase PostgreSQL

1. Create a free project at supabase.com.
2. Project Settings → Database → Connection string → URI. Copy it.
3. In `backend/.env`, set:
   ```
   DATABASE_URL=postgresql+psycopg2://postgres:<your-password>@<your-host>:5432/postgres?sslmode=require
   ```
   (rewrite the scheme from `postgresql://` to `postgresql+psycopg2://` — SQLAlchemy needs the driver
   named explicitly; keep `?sslmode=require`, Supabase requires TLS.)
4. `python main.py` will create all tables and seed demo data automatically the first time it runs
   against that database — same as Phase 1's SQLite auto-init, just against Postgres now.

`database.py` will now refuse to start if `DATABASE_URL` is unset or still points at `sqlite:///...`,
with an explicit error message telling you what to fix.

## ML model files

Running `python main.py` or any test that calls `predict_eta()` will auto-generate
`ml/training_data.csv` and train+save `ml/model.pkl` on first use if they don't exist yet
(a few seconds). To do it explicitly:
```powershell
python -m ml.generate_data   # writes ml/training_data.csv
python -m ml.train_model     # trains, saves ml/model.pkl + ml/model_metadata.json, prints MAE/R2
```
Both files are gitignored (`*.csv` isn't currently ignored — only `*.pkl` is; add `ml/training_data.csv`
to `.gitignore` yourself if you don't want it committed) since they're fully regenerable.

## Verification status (please read)

Same situation as Phase 1: I have no internet access in the sandbox I built this in, so I could not
`pip install fastapi`/`sqlalchemy`/`psycopg2` there to run the live server or the DB-backed tests.
What's different this time is that **scikit-learn, pandas, numpy, and joblib were already available**
in that sandbox (no install needed), so I could and did actually execute the ML and simulation-engine
logic for real:

- **Trained the actual ETA model**: MAE 3.30 minutes, R² 0.9716 on held-out data. Feature importances
  are physically sensible (distance 71%, traffic 22%, stops 4%, the rest small).
- **Ran real predictions**: confirmed severe traffic roughly doubles predicted ETA vs. low traffic at
  the same distance; confirmed longer distance increases ETA; confirmed invalid `traffic_level`/`priority`
  correctly raise `ValueError`.
- **Ran the simulation engine standalone**: verified distance calculation, lat/lng interpolation along
  a multi-waypoint route, progress-percentage tracking, and completion detection — all four
  `TestSimulationEngineUnit` tests pass as written, executed directly (not just compiled).
- **Ran the K-Means clustering + TSP integration standalone**: confirmed it correctly separates two
  geographic clusters and produces a valid warehouse-out-and-back sequence.
- **All 6 `TestMLPredictUnit` tests and all 4 `TestSimulationEngineUnit` tests were manually executed
  (not just read) and pass.**
- Every file (old and new) still syntax-compiles (`py_compile`), and I re-ran a full manual cross-check
  of every internal `from X import Y` against what's actually defined in `X` — this caught the Phase 1
  `ALGORITHMS` export bug (already fixed) and confirmed no equivalent issue in the Phase 2 additions.
- I also found and fixed a real concurrency bug before you saw this code: `asyncio.create_task()`
  cannot be called from a thread-pool-executed `def` endpoint (FastAPI runs plain `def` handlers in a
  worker thread with no running event loop). `start_simulation` and `resume_simulation` are `async def`
  specifically so the WebSocket broadcast loop can actually start.

**Not verified by me**: the full FastAPI/SQLAlchemy/Postgres request-response cycle — routers, DB
writes, JWT flow, the WebSocket endpoint under real ASGI, and all four new *integration* test classes
(`TestMLPredictAPI`, `TestBatchingAPI`, `TestSimulationAPI`, `TestSimulationWebSocket`,
`TestAnalyticsSummary`). Please run `pytest -v` on your machine, with a real Supabase database
configured, and tell me what fails — if anything does, I'll fix it before Phase 3.

## Windows + VS Code setup

Open the `backend` folder in VS Code, then in the integrated terminal (PowerShell):

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
or use Command Prompt instead: `venv\Scripts\activate.bat`

Then, with the venv active:

```powershell
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your Supabase connection string (see "Database" above).
Then:

```powershell
python main.py
```

You should see Uvicorn start on `http://localhost:8000`. On first run it prints the seed summary
(demo user, locations, drivers, orders, traffic events). Open `http://localhost:8000/docs`, log in
with `admin@intelliroute.com` / `Admin@123`, click **Authorize**, and try:

- `POST /api/ml/predict-eta` with `{"distance_km": 8, "traffic_level": "high"}`
- `POST /api/batches/create` with `{"orders_per_batch": 3}`
- `POST /api/simulation/start` (after assigning at least one order to a driver — `POST
  /api/orders/dispatch-next` does this automatically)
- `GET /api/analytics/summary`

For the WebSocket, use a simple browser console or a tool like `websocat`/Postman against
`ws://localhost:8000/ws/simulation` — you should see one JSON state message per second while a
simulation is running.

### Running the tests

Set `TEST_DATABASE_URL` in `.env` to a **separate, disposable** Postgres database first — tests drop
and recreate all tables at that URL. If you skip this, tests fall back to your real `DATABASE_URL` and
will wipe it; `conftest.py` prints a warning either way.

```powershell
pytest -v
```

This runs Phase 1's algorithm/API tests plus Phase 2's ML/batching/simulation/analytics tests. The
pure-logic classes (`TestMLPredictUnit`, `TestSimulationEngineUnit`, `TestKMeansClusteringUnit`) don't
touch the database at all and are the fastest signal if something's wrong — if those fail, the issue is
in the algorithm/ML code itself, not the DB/API wiring.

# Phase 3 — React Frontend

A complete Vite + React frontend connected to the existing Phase 1/2 FastAPI backend — no mock data, no fake endpoints, no backend changes required.

## What's actually implemented

- **Auth**: login, signup, JWT stored in `localStorage`, Axios request interceptor attaches `Authorization: Bearer <token>` to every call, response interceptor forces logout + redirect on 401. `/api/auth/me` validates the token on page load rather than trusting the cached user blindly. Protected routes redirect to `/login`; visiting `/login` or `/signup` while authenticated redirects to `/dashboard`.
- **Google login**: shown as a disabled button ("backend configuration required") rather than faked — the backend has no OAuth endpoint, so pretending it works would violate the brief's own "no fake functionality" rule.
- **Dashboard**: 8 stat cards, order-status bar chart, priority-distribution pie chart, fleet-utilization bar chart, priority queue panel with a working "Dispatch next" button, a live-simulation snapshot panel, a map of current driver/pending-order locations, and a recent-orders table — every number comes from `GET /api/analytics/summary`, `/api/orders`, `/api/orders/priority-queue`, `/api/drivers`, `/api/simulation/state`.
- **Orders**: full CRUD against `/api/orders`, client-side search/priority-filter/sort (backend has no search or priority-filter query params, so those run in the browser over the fetched list — status filtering does use the backend's real `status_filter` param), a create form that resolves pickup/delivery lat/lng from `/api/routes/locations` (so orders land on real graph nodes the routing/simulation engine can use), an edit form scoped to exactly the three fields `OrderUpdate` accepts (status, assigned_driver_id, priority), and a working "Dispatch next" button.
- **Fleet**: tabbed Drivers/Vehicles views, full CRUD against `/api/drivers` and `/api/vehicles`, with the same create/update field split the backend schemas enforce.
- **Routes**: pick start/destination from the real location list, choose any of the 6 real algorithms, run `/api/routes/optimize`, see distance/time/nodes-explored/path, and see the resolved path drawn as a polyline on the map.
- **Batches**: trigger `/api/batches/create` (K-Means clustering happens entirely in the backend — the frontend just calls it), list batches, expand a batch to lazy-load its order IDs via `/api/batches/{id}`.
- **Live simulation**: a real `WebSocket` connection to `/ws/simulation` with exponential-backoff auto-reconnect (visible connection-status indicator), Start/Pause/Resume/Stop/Reset wired to the actual REST control endpoints, live-updating progress bars and a map with driver markers positioned from the real `lat`/`lng` the engine broadcasts every tick — nothing here is simulated client-side.
- **Analytics**: status/priority/utilization charts plus an embedded ETA-prediction widget, all from `/api/analytics/summary` and `/api/ml/predict-eta`.
- **Error handling**: every data-fetching component has loading/error/empty states; the Axios interceptor normalizes 401/403/404/422/500/network errors into readable messages.
- **Responsive**: sidebar collapses to an off-canvas drawer under 900px, chart grids collapse to one column under 1024px, forms stack under 640px.

## Files created

```
frontend/
├── package.json, vite.config.js, index.html, .env.example
└── src/
    ├── main.jsx, App.jsx
    ├── api/            axios.js, auth.js, orders.js, drivers.js, vehicles.js,
    │                    routes.js, analytics.js, ml.js, batches.js, simulation.js
    ├── components/     Navbar.jsx, Sidebar.jsx, Layout.jsx, StatCard.jsx, OrderTable.jsx,
    │                    DriverTable.jsx, VehicleTable.jsx, PriorityQueue.jsx, MapView.jsx,
    │                    RoutePanel.jsx, ETAWidget.jsx, BatchCard.jsx, LiveSimulation.jsx,
    │                    Loading.jsx, ErrorState.jsx, EmptyState.jsx, Badge.jsx, Modal.jsx
    ├── pages/          Login.jsx, Signup.jsx, Dashboard.jsx, Orders.jsx, Fleet.jsx,
    │                    Routes.jsx, Batches.jsx, Simulation.jsx, Analytics.jsx
    ├── context/        AuthContext.jsx
    └── styles/         global.css
```
(`Layout.jsx`, `ErrorState.jsx`, `EmptyState.jsx`, `Badge.jsx`, `Modal.jsx` weren't in the original file list but were necessary — every data view needs loading/error/empty states and status/priority badges, and routing needed a shell component.)

## Backend files modified

**None.** CORS in `backend/main.py` already allowed `http://localhost:5173` / `http://127.0.0.1:5173` since Phase 1 — Vite's default dev port — so no backend change was required for the frontend to talk to it.

## Design system

Indigo/coral palette (`#4f46e5` primary, `#ff5a36` accent) on a cool neutral background — deliberately not the warm-cream/terracotta or near-black/neon defaults. Space Grotesk for headings and numbers, Inter for UI text. Full token/spacing/component system in `src/styles/global.css` (cards, badges, tables, forms, modals, the sidebar/navbar shell, priority-queue rows, simulation progress bars) rather than one-off inline styles.

## Verification status (please read)

Same sandbox, same no-internet constraint as Phase 1/2 — I could not `npm install` here (confirmed: `npm install react` returns `403 Forbidden` from the registry with no packages cached). **What's different this time**: Node.js *is* installed in this sandbox, and bundled inside an unrelated pre-installed tool (`tsx`) is a copy of **esbuild**, which has a real JSX/JS parser and a real ES-module linker. I used it directly (not through Vite, since Vite itself couldn't be installed) to:

1. **Parse every one of the 39 `.js`/`.jsx` files individually** — all 39 parse with zero syntax errors (verified after discovering plain `node --check` can't parse JSX at all — confirmed by testing on this exact codebase and by testing on a renamed `.mjs` copy of `App.jsx`, which fails with `SyntaxError: Unexpected token '<'`; esbuild's dedicated JSX loader was needed and used instead).
2. **Bundled the entire app from `main.jsx`**, externalizing only the actual npm packages (React, React Router, Axios, Leaflet, React-Leaflet, Recharts, Lucide) so every *local* import had to resolve for real. This produced a clean 116.5kb bundle with **zero errors and zero warnings** — meaning every relative import path across all 39 files points at a file that actually exists, and every named import (e.g. `import { StatusBadge, PriorityBadge } from "./Badge"`) matches an export that actually exists in that file.
3. **Sanity-checked that this check isn't a rubber stamp**: I deliberately broke an import (`import { NonExistentExport } from "./Badge"` in `StatCard.jsx`), re-ran the exact same bundle command, and confirmed it correctly failed with `No matching export in "src/components/Badge.jsx" for import "NonExistentExport"` — then reverted the change and re-confirmed the bundle was clean again.

**What this does NOT verify**: actual runtime behavior in a browser (React rendering, hook behavior, CSS layout, the WebSocket reconnect logic under real network conditions, Leaflet actually painting tiles), and it does not verify against the *live* backend since I have no running Postgres/FastAPI instance here either. Every endpoint path, request-body shape, and response-field name in the `api/` layer was matched by hand against the actual Phase 1/2 router and schema source files (not from memory of what I intended to build), and I've called that out inline as comments in each `api/*.js` file so you can spot-check it yourself. The frontend is included in this final repository. Browser rendering and live database/runtime behavior still depend on the local environment, Supabase configuration, and installed npm/Python dependencies.

## Windows + VS Code setup

With the backend already running (see Phase 1/2 sections above — `python main.py` from `backend/`, in its own terminal), open a **second** terminal:

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open `http://localhost:5173`.

### Test login
Log in with the seeded demo account: `admin@intelliroute.com` / `Admin@123`. Or click "Sign up" and create a new account — it logs you in immediately (the backend's signup endpoint returns a token, same as login).

### Test orders
Go to **Orders** → **New order**. Pick a pickup and delivery location from the dropdowns (these come from `/api/routes/locations`, the same graph the routing engine uses), set a priority, submit. It should appear in the table and in the Dashboard's priority queue panel. Try **Dispatch next** — it should assign the highest-priority pending order to the nearest available driver and update that order's status.

### Test live simulation
First, dispatch or manually assign at least one order to a driver (Orders page, or the Dashboard's dispatch button). Go to **Simulation** → **Start**. You should see the connection indicator turn "Live", a driver marker appear on the map, and its progress bar/percentage advance roughly once per second — this is the same `/ws/simulation` broadcast from `simulation/engine.py`, not a client-side animation. **Pause**/**Resume**/**Stop**/**Reset** all call the real REST endpoints.

### Test ML ETA
Go to **Analytics** (or the Dashboard) and use the ETA prediction widget: enter a distance and traffic level, submit, and you'll get back a real prediction from the trained `RandomForestRegressor` (auto-trained on first backend startup if `ml/model.pkl` doesn't exist yet).

### Test K-Means batching
Create a handful of pending orders with different delivery locations (Orders page), then go to **Batches** → set "Orders per batch" → **Create batches**. You should see one or more batch cards; expanding one lazy-loads its order IDs via `/api/batches/{id}`. If you get a 404 ("No unbatched pending orders available"), create more pending orders first — every order defaults to `pending` until assigned.

## Final project status

IntelliRoute now contains all three development phases in one repository:

- Phase 1: FastAPI backend, Supabase/PostgreSQL database, authentication, CRUD APIs, routing algorithms, Priority Queue and TSP/2-opt.
- Phase 2: Random Forest ETA prediction, K-Means batching, live WebSocket simulation and analytics.
- Phase 3: React + Vite frontend with dashboard, orders, fleet, routes, batches, simulation, analytics, Leaflet map and API integration.

No API keys, passwords or production secrets are included in the repository. Configure them locally through the provided `.env` files.

## Running the complete application

Start the backend first, then open a second terminal for the frontend. The backend should be available at `http://127.0.0.1:8000` and the frontend at `http://localhost:5173`.
