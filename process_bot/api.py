from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from process_bot.database import get_db, init_db
from process_bot import schemas, services


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_BUILD_DIR = BASE_DIR / "static" / "app"
FRONTEND_ASSETS_DIR = FRONTEND_BUILD_DIR / "assets"

app = FastAPI(title="Process Tracker API", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR)), name="assets")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse, response_model=None)
def dashboard(request: Request):
    del request
    index_file = FRONTEND_BUILD_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse(
        "<html><body><p>Frontend build not found. Run <code>npm install</code> then <code>npm run build</code>.</p></body></html>"
    )


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/companies", response_model=list[schemas.CompanyResponse])
def get_companies(db: Session = Depends(get_db)) -> list[schemas.CompanyResponse]:
    return services.list_companies(db)


@app.post("/api/companies", response_model=schemas.CompanyResponse)
def create_company(payload: schemas.CompanyCreate, db: Session = Depends(get_db)) -> schemas.CompanyResponse:
    company = services.get_or_create_company(db, payload.name)
    db.commit()
    return company


@app.post("/api/company-aliases")
def create_company_alias(payload: schemas.CompanyAliasCreate, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        alias = services.create_company_alias(db, payload.company_slug, payload.alias)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return {"company_slug": payload.company_slug, "alias": alias.alias}


@app.get("/api/stats/global", response_model=schemas.GlobalStatsResponse)
def get_global_stats(db: Session = Depends(get_db)) -> schemas.GlobalStatsResponse:
    return services.global_stats(db)


@app.get("/api/stats/company/{company_slug}", response_model=schemas.CompanyStatsResponse)
def get_company_stats(company_slug: str, db: Session = Depends(get_db)) -> schemas.CompanyStatsResponse:
    stats = services.company_stats(db, company_slug)
    if not stats:
        raise HTTPException(status_code=404, detail="Company not found")
    return stats


@app.get("/api/stats/trends", response_model=list[schemas.TrendPoint])
def get_trends(
    company_slug: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[schemas.TrendPoint]:
    return services.event_trends(db, company_slug=company_slug)


@app.get("/api/me/processes", response_model=list[schemas.ProcessEventResponse])
def get_my_processes(
    discord_user_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> list[schemas.ProcessEventResponse]:
    return services.list_user_processes(db, discord_user_id)


@app.post("/api/process-events", response_model=schemas.ProcessEventResponse)
def create_process_event(
    payload: schemas.ProcessEventCreate,
    db: Session = Depends(get_db),
) -> schemas.ProcessEventResponse:
    try:
        event = services.create_process_event(db, payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(event)
    return services.serialize_process_event(event)


@app.patch("/api/process-events/{event_id}", response_model=schemas.ProcessEventResponse)
def update_process_event(
    event_id: int,
    payload: schemas.ProcessEventUpdate,
    db: Session = Depends(get_db),
) -> schemas.ProcessEventResponse:
    try:
        event = services.update_process_event(db, event_id, payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not event:
        raise HTTPException(status_code=404, detail="Process event not found")
    db.commit()
    db.refresh(event)
    return services.serialize_process_event(event)


@app.delete("/api/process-events/{event_id}")
def delete_process_event(event_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    deleted = services.delete_process_event(db, event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Process event not found")
    db.commit()
    return {"deleted": True}


@app.get("/api/admin/process-events", response_model=list[schemas.ProcessEventResponse])
def get_all_process_events(db: Session = Depends(get_db)) -> list[schemas.ProcessEventResponse]:
    return services.list_all_process_events(db)
