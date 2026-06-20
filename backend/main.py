from fastapi import FastAPI

from app.routers import analyze, auth, authorities, complaints, contractors, dashboard, roads

app = FastAPI(title="RoadWatch API")

app.include_router(auth.router)
app.include_router(roads.router)
app.include_router(complaints.router)
app.include_router(authorities.router)
app.include_router(contractors.router)
app.include_router(dashboard.router)
app.include_router(analyze.router)


@app.get("/")
def view_root():
    return {"message": "RoadWatch API"}
