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
    name: str
    time: str
    dose: int

class Reminder(ReminderIn):
    id: str

# ===== PAMIĘĆ (na razie) =====
reminders: list[Reminder] = []

# ---- API ----
@app.get("/api/reminders")
def list_reminders():
    return reminders

@app.post("/api/reminders")
def add_reminder(data: ReminderIn):
    r = Reminder(id=str(uuid.uuid4()), **data.dict())
    reminders.append(r)
    return r

@app.put("/api/reminders/{rid}")
def update_reminder(rid: str, data: ReminderIn):
    for i, r in enumerate(reminders):
        if r.id == rid:
            reminders[i] = Reminder(id=rid, **data.dict())
            return reminders[i]
    raise HTTPException(404, "Not found")

@app.delete("/api/reminders/{rid}")
def delete_reminder(rid: str):
    global reminders
    before = len(reminders)
    reminders = [r for r in reminders if r.id != rid]
    if len(reminders) == before:
        raise HTTPException(404, "Not found")
    return {"status": "deleted"}