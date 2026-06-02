from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent

@app.get("/", response_class=HTMLResponse)
def weekly_report():
    html_path = BASE_DIR / "weekly_report.html"
    return html_path.read_text(encoding="utf-8")

@app.get("/sankey", response_class=HTMLResponse)
def sankey_preview():
    html_path = BASE_DIR / "sankey_preview.html"
    return html_path.read_text(encoding="utf-8")

@app.get("/weekly_report.png")
def weekly_report_image():
    image_path = BASE_DIR / "weekly_report.png"
    return FileResponse(image_path, media_type="image/png")