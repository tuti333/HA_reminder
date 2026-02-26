import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel

app = FastAPI()

www_path = Path(__file__).parent / "www"

# Serwowanie plików statycznych
app.mount("/static", StaticFiles(directory=www_path), name="static")

@app.get("/", response_class=HTMLResponse)
@app.get("//", response_class=HTMLResponse)
def index():
    return (www_path / "index.html").read_text(encoding="utf-8")

# ===== MODELE =====
class ReminderIn(BaseModel):
    # allow missing/blank person from the UI and provide a safe default
    person: str = ""
    name: str
    time: str
    dose: int

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
            reminders = [Reminder(**item) for item in raw]
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