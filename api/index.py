from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent

# این خط باعث می‌شود فایل‌های داخل پوشه assets روی سایت قابل دسترسی باشند
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")

@app.get("/", response_class=HTMLResponse)
def home():
    html_path = BASE_DIR / "weekly_report.html"
    return html_path.read_text(encoding="utf-8")

@app.get("/digital", response_class=HTMLResponse)
def digital_hub():
    html_path = BASE_DIR / "page" / "index.html"
    return html_path.read_text(encoding="utf-8")

@app.get("/seo", response_class=HTMLResponse)
def seo_report():
    html_path = BASE_DIR / "seo" / "seo_weekly_report.html"
    return html_path.read_text(encoding="utf-8")

@app.get("/weekly_report.png")
def weekly_report_image():
    image_path = BASE_DIR / "weekly_report.png"
    return FileResponse(image_path, media_type="image/png")