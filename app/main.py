import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, field_validator
from typing import List, Union

app = FastAPI()

# middleware will collapse repeated slashes so that "/foo//bar" and "/foo/bar"
# are treated identically; allows ingress to send a double-slash prefix without
# requiring every route to redeclare it.
import re
from starlette.requests import Request

@app.middleware("http")
async def normalize_path(request: Request, call_next):
    # modify the scope path in-place before routing
    request.scope["path"] = re.sub(r"/{2,}", "/", request.scope["path"])
    return await call_next(request)

www_path = Path(__file__).parent / "www"

# Serwowanie plików statycznych
app.mount("/static", StaticFiles(directory=www_path), name="static")

# templates support so we can inject current time into HTML
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from datetime import datetime

templates = Jinja2Templates(directory=str(www_path))

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # use server/system time (should match Home Assistant) on each request
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return templates.TemplateResponse("index.html", {"request": request, "current_time": now})

# ===== MODELE =====
class ReminderIn(BaseModel):
    # allow missing/blank person from the UI and provide a safe default
    person: str = ""
    name: str
    # time periods may be multiple values
    time: List[Union[int,str]]
    dose: int = 1

    @field_validator("time", mode="before")
    def _coerce_time(cls, v):
        if v is None:
            return []
        if isinstance(v, (str, int)):
            return [str(v)]
        if isinstance(v, list):
            return [str(x) for x in v]
        raise ValueError("invalid time value")

    @field_validator("dose", mode="before")
    def _coerce_dose(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return 1
        if isinstance(v, str):
            try:
                return int(v)
            except Exception:
                raise ValueError("dose must be an integer")
        return v

class Reminder(ReminderIn):
    id: str

# ===== PAMIĘĆ (plikowa) =====
from pathlib import Path
import json

REMINDERS_FILE = Path(__file__).parent / "reminders.json"


# global storage variable; populated from disk on startup
reminders: list[Reminder] = []


def load_reminders() -> None:
    """Read reminders from REMINDERS_FILE if it exists.
    Any errors during load are logged to console and ignored, leaving
    the in-memory list empty (so the server still works).
    """
    global reminders
    if REMINDERS_FILE.exists():
        try:
            raw = json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
            # migrate old entries
            cleaned = []
            for item in raw:
                if "person" not in item:
                    item["person"] = ""
                if "time" in item and not isinstance(item["time"], list):
                    item["time"] = [str(item["time"]) ]
                cleaned.append(item)
            reminders = [Reminder(**item) for item in cleaned]
        except Exception as exc:
            # not fatal; keep empty list and print error for debugging
            print(f"failed to load reminders: {exc}")
            reminders = []


def save_reminders() -> None:
    """Write the current `reminders` list to disk.
    Overwrites the file atomically by writing a temporary file and
    renaming it so that concurrent reads don't see partial data.
    """
    try:
        temp = REMINDERS_FILE.with_suffix(".tmp")
        temp.write_text(json.dumps([r.dict() for r in reminders], ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(REMINDERS_FILE)
    except Exception as exc:
        # printing errors is fine; in production consider logging
        print(f"failed to save reminders: {exc}")


# populate on import/startup
load_reminders()

# ---- API ----
@app.get("/api/reminders")
def list_reminders():
    return reminders

@app.post("/api/reminders")
def add_reminder(data: ReminderIn):
    r = Reminder(id=str(uuid.uuid4()), **data.dict())
    reminders.append(r)
    save_reminders()
    return r

@app.put("/api/reminders/{rid}")
def update_reminder(rid: str, data: ReminderIn):
    for i, r in enumerate(reminders):
        if r.id == rid:
            reminders[i] = Reminder(id=rid, **data.dict())
            save_reminders()
            return reminders[i]
    raise HTTPException(404, "Not found")

@app.delete("/api/reminders/{rid}")
def delete_reminder(rid: str):
    global reminders
    before = len(reminders)
    reminders = [r for r in reminders if r.id != rid]
    if len(reminders) == before:
        raise HTTPException(404, "Not found")
    save_reminders()
    return {"status": "deleted"}


# ===== DZIŚ / SCHEDULE =====
from collections import defaultdict

PERIOD_MAP = {"1": "rano", "2": "popołudnie", "3": "wieczór"}


@app.get("/api/today")
def today_schedule():
    """Return reminders arranged for the current day grouped by person and period.

    Behavior:
    - period values `1`, `2`, `3` map to `rano`, `popołudnie`, `wieczór`.
    - reminders with an empty `time` list are shown in all three periods.
    - unknown time values are grouped under `unspecified`.
    """
    now = datetime.now()
    schedule: dict = {}

    # ensure every known person has an entry
    for r in reminders:
        schedule.setdefault(r.person, {"rano": [], "popołudnie": [], "wieczór": [], "unspecified": []})

    for r in reminders:
        times = r.time or []
        if not times:
            # treat unspecified time as applicable to all periods
            for label in ("rano", "popołudnie", "wieczór"):
                schedule.setdefault(r.person, {"rano": [], "popołudnie": [], "wieczór": [], "unspecified": []})[label].append(r.dict())
        else:
            for t in times:
                label = PERIOD_MAP.get(str(t))
                if label:
                    schedule.setdefault(r.person, {"rano": [], "popołudnie": [], "wieczór": [], "unspecified": []})[label].append(r.dict())
                else:
                    schedule.setdefault(r.person, {"rano": [], "popołudnie": [], "wieczór": [], "unspecified": []})["unspecified"].append(r.dict())

    return {"date": now.strftime("%Y-%m-%d"), "schedule": schedule}