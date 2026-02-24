from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

www_path = Path(__file__).parent / "www"

# Serwowanie plików statycznych
app.mount("/static", StaticFiles(directory=www_path), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    return (www_path / "index.html").read_text(encoding="utf-8")
