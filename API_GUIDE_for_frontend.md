# RoadWatch API — Frontend Integration Guide

Base URL (local dev): `http://localhost:8000`

All request/response bodies are JSON unless noted (complaint submission uses multipart form-data for the image).

---

## Authentication

Most endpoints are public (read-only data). A few require a logged-in user. Send the token as:
```
Authorization: Bearer <access_token>
```

### `POST /auth/signup`
Body:
```json
{ "name": "Jane Doe", "email": "jane@mail.com", "phone": "9876543210", "password": "secret123", "role": "citizen" }
```
`role` is one of `citizen` / `authority` / `admin` (default `citizen`). Returns the created user (no password).

### `POST /auth/login`
Body: `{ "email": "...", "password": "..." }`
Returns: `{ "access_token": "...", "token_type": "bearer" }` — store this token, attach to future requests.

### `GET /auth/me` 🔒
Returns the currently logged-in user's profile. Useful to check if a stored token is still valid.

---

## Roads (Feature 01 — Tap-a-Road)

### `GET /roads/by-osm/{osm_id}`
**Use this first** when the citizen taps a road on the Leaflet/OSM map — pass the road's OSM way ID from the map's GeoJSON data. Exact match, fastest.

### `GET /roads/nearby?lat=&lng=&radius=`
Fallback if no `osm_id` is available (e.g. complaint filed from GPS without a map tap). `radius` is in km, default 2, max 50. Returns a list of nearby roads sorted by distance.

### `GET /roads/{sl_no}`
Full metadata for one road: name, type, contractor, engineers + contacts, budget figures, health score, complaint count, geometry (for drawing on map).

### `GET /roads/{sl_no}/budget`
Budget trail (Feature 06): sanctioned/released/spent/unspent, percentage released/spent, plus two boolean flags:
- `flag_released_exceeds_sanctioned`
- `flag_large_spend_gap`

### `GET /roads/{sl_no}/health-score`
Live-computed health score (Feature 04), not the static CSV value. Includes `days_since_last_repair`, `open_complaints`, `pct_budget_used`, `repair_count`, and a human-readable `condition` string.

### `GET /roads/{sl_no}/timeline`
Chronological list of `Built` / `Repaired` / `Complaint` events for the repair-history view (Feature 05).

### `POST /roads/{sl_no}/repairs` 🔒 (authority/admin only)
Add a new repair event to a road's timeline.
Body:
```json
{ "event_type": "Repaired", "event_date": "2026-03-15", "notes": "Resurfaced 2km stretch" }
```

---

## Complaints (Feature 02 — AI Complaint Portal, Feature 03 — Routing)

### `POST /complaints` 🔒 — multipart/form-data
Fields: `road_sl_no` (int), `file` (image), optionally `latitude` / `longitude`.
The backend runs the AI model on the image, detects issue type + severity, auto-assigns the correct authority based on road type (routing happens here automatically), generates a `tracking_id`, and computes the SLA `response_deadline`. Returns the full complaint record.

### `GET /complaints?road_sl_no=` (optional filter)
List complaints, most recent first.

### `GET /complaints/{tracking_id}`
Look up a complaint by its tracking ID — use this for the "track my complaint" screen.

### `POST /complaints/escalate-overdue`
Admin/cron-triggered. Scans for complaints past their SLA deadline and marks them escalated. Not typically called by the regular citizen UI.

---

## Authorities (Feature 03 — Routing transparency)

### `GET /authorities`
List of all routing authorities with their jurisdiction (road type + division) and escalation path. Useful for an "accountability" info page showing how routing works.

---

## Contractors & Dashboard (Feature 04, 09)

### `GET /contractors/leaderboard`
Public contractor scoring leaderboard, sorted worst-to-best. Each item has `red_flagged: true` if score < 40 — use this to visually flag contractors in red on the UI.

### `GET /dashboard?division=` (optional filter)
City/district summary stats: total roads, condition split (good/average/poor with percentages), this month's complaint stats, average resolution time, and the lowest-scoring contractor. Good for the public-facing landing dashboard.

---

## AI Image Analysis (standalone, used internally by complaints)

### `POST /analyze/image`
Multipart form-data with `file`. Returns raw detection results (damage type, confidence, severity, suggested SLA, routing target, bounding boxes). You generally won't call this directly from the frontend — `POST /complaints` already does this internally — but it's available if you want a "preview before submitting" feature.

---

## Quick reference — what needs login (🔒)
- `POST /complaints`
- `POST /roads/{sl_no}/repairs` (authority/admin role only)
- `GET /auth/me`

Everything else is public/read-only.
